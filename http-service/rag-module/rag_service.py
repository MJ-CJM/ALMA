import os
import fitz  # PyMuPDF
from typing import List, Dict, Any
import numpy as np
from openai import OpenAI
from pymilvus import MilvusClient
import json
import hashlib
import time

class RAGService:
    def __init__(self):
        # 初始化 OpenAI 客户端用于 embedding
        self.client = OpenAI(
            api_key="sk-1f0b08f7ee4742c39dbb63254f3db29e",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # Milvus 连接配置
        self.collection_name = "rag_documents"
        self.dim = 1024  # embedding 维度
        
        # 确保 db_data 目录存在（本地数据库）
        # self.db_data_dir = "db_data"
        # os.makedirs(self.db_data_dir, exist_ok=True)
        
        # 文件管理
        self.processed_files = set()  # 已处理的文件集合
        self.file_hash_map = {}  # 文件哈希映射
        
        # 连接 Milvus
        self._connect_milvus()
        self._create_collection()
        
        # 自动加载 PDF 文件
        self.auto_load_pdf_files()
    
    # def _connect_milvus(self):
    #     """连接 Milvus Lite 本地数据库"""
    #     max_retries = 3
    #     retry_delay = 1
    #
    #     for attempt in range(max_retries):
    #         try:
    #             db_file = os.path.join(self.db_data_dir, "milvus_lite.db")
    #
    #             # 检查文件是否被锁定
    #             if os.path.exists(db_file):
    #                 try:
    #                     # 尝试打开文件检查是否被锁定
    #                     with open(db_file, 'r+b') as f:
    #                         pass
    #                 except (IOError, PermissionError):
    #                     print(f"数据库文件被锁定，等待 {retry_delay} 秒后重试...")
    #                     time.sleep(retry_delay)
    #                     retry_delay *= 2
    #                     continue
    #
    #             self.milvus_client = MilvusClient(db_file)
    #             print(f"成功连接到 Milvus Lite，数据存储在: {db_file}")
    #             return
    #
    #         except Exception as e:
    #             print(f"连接尝试 {attempt + 1}/{max_retries} 失败: {e}")
    #             if attempt < max_retries - 1:
    #                 print(f"等待 {retry_delay} 秒后重试...")
    #                 time.sleep(retry_delay)
    #                 retry_delay *= 2
    #             else:
    #                 print("所有连接尝试都失败，请检查数据库文件是否被其他进程占用")
    #                 raise

    def _connect_milvus(self):
        """连接远程 Milvus 服务器"""
        try:
            self.milvus_client = MilvusClient(
                uri="http://101.34.214.7:6002"  # 如 http://101.34.214.7:6002
            )
            print("成功连接到远程 Milvus 服务器")
        except Exception as e:
            print(f"连接 Milvus 失败: {e}")
            raise
    
    def _create_collection(self):
        """创建 Milvus 集合"""
        try:
            # 检查集合是否存在
            collections = self.milvus_client.list_collections()
            if self.collection_name in collections:
                print(f"集合 {self.collection_name} 已存在")
                return
            
            # 创建集合
            self.milvus_client.create_collection(
                collection_name=self.collection_name,
                dimension=self.dim,
                primary_field_name="id",
                vector_field_name="embedding"
            )
            print(f"创建集合 {self.collection_name}")
        except Exception as e:
            print(f"创建集合失败: {e}")
            raise
    
    def _get_file_hash(self, file_path: str) -> str:
        """获取文件的 MD5 哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _load_processed_files_info(self):
        """从数据库加载已处理文件信息"""
        try:
            # 查询所有文件哈希
            results = self.milvus_client.query(
                collection_name=self.collection_name,
                filter="",
                output_fields=["filename", "file_hash"],
                limit=1000  # 添加 limit 参数
            )
            
            for result in results:
                filename = result.get("filename")
                file_hash = result.get("file_hash")
                if filename and file_hash:
                    self.processed_files.add(filename)
                    self.file_hash_map[filename] = file_hash
            
            print(f"已加载 {len(self.processed_files)} 个已处理文件信息")
        except Exception as e:
            print(f"加载已处理文件信息失败: {e}")
    
    def auto_load_pdf_files(self, pdf_dir: str = "data/pdf"):
        """自动加载 PDF 文件"""
        print("开始自动加载 PDF 文件...")
        
        # 加载已处理文件信息
        self._load_processed_files_info()
        
        if not os.path.exists(pdf_dir):
            print(f"目录 {pdf_dir} 不存在")
            return
        
        new_files = []
        for filename in os.listdir(pdf_dir):
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(pdf_dir, filename)
                file_hash = self._get_file_hash(pdf_path)
                
                # 检查文件是否已处理或已更新
                if filename not in self.processed_files or self.file_hash_map.get(filename) != file_hash:
                    print(f"处理新文件或更新文件: {filename}")
                    
                    # 提取文本
                    text_segments = self.extract_text_from_pdf(pdf_path)
                    if not text_segments:
                        continue
                    
                    # 生成 embeddings
                    embeddings = self.get_embeddings(text_segments)
                    if not embeddings:
                        continue
                    
                    # 确保文本和 embedding 数量一致
                    min_len = min(len(text_segments), len(embeddings))
                    text_segments = text_segments[:min_len]
                    embeddings = embeddings[:min_len]
                    
                    # 准备数据，包含 id 字段
                    data = []
                    for i in range(min_len):
                        data.append({
                            "id": i,  # 添加 id 字段
                            "text": text_segments[i],
                            "embedding": embeddings[i],
                            "filename": filename,
                            "file_hash": file_hash
                        })
                    
                    # 插入数据到 Milvus
                    self.milvus_client.insert(
                        collection_name=self.collection_name,
                        data=data
                    )
                    print(f"成功插入 {len(data)} 个文本段")
                    
                    # 更新文件信息
                    self.processed_files.add(filename)
                    self.file_hash_map[filename] = file_hash
                    new_files.append(filename)
        
        if new_files:
            print(f"成功处理 {len(new_files)} 个新文件: {new_files}")
        else:
            print("没有新的 PDF 文件需要处理")
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[str]:
        """从 PDF 文件中提取文本并按段切分"""
        try:
            doc = fitz.open(pdf_path)
            text_segments = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                # 按段落切分文本
                paragraphs = text.split('\n\n')
                for paragraph in paragraphs:
                    paragraph = paragraph.strip()
                    if paragraph and len(paragraph) > 10:  # 过滤太短的段落
                        text_segments.append(paragraph)
            
            doc.close()
            return text_segments
        except Exception as e:
            print(f"提取 PDF 文本失败: {e}")
            return []
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """使用 Qwen3-Embedding 生成向量嵌入"""
        try:
            # 限制输入长度
            if len(texts) > 10:
                texts = texts[:10]
            
            # 检查每个文本的长度
            valid_texts = []
            for text in texts:
                if len(text) <= 8192:  # 限制 token 长度
                    valid_texts.append(text)
                else:
                    # 如果文本太长，截断
                    valid_texts.append(text[:8192])
            
            if not valid_texts:
                return []
            
            response = self.client.embeddings.create(
                model="text-embedding-v4",
                input=valid_texts,
                dimensions=self.dim,
                encoding_format="float"
            )
            
            embeddings = []
            for embedding in response.data:
                embeddings.append(embedding.embedding)
            
            return embeddings
        except Exception as e:
            print(f"生成 embedding 失败: {e}")
            return []
    
    def search_similar_texts(self, query: str, top_k: int = 5, filename: str = None) -> List[Dict[str, Any]]:
        """搜索相似文本，支持按文件名过滤"""
        try:
            # 生成查询的 embedding
            query_embeddings = self.get_embeddings([query])
            if not query_embeddings:
                return []
            
            # 构建查询条件
            filter_expr = ""
            if filename:
                filter_expr = f'filename == "{filename}"'
            
            # 搜索相似向量 - 使用简化的参数
            results = self.milvus_client.search(
                collection_name=self.collection_name,
                data=[query_embeddings[0]],
                anns_field="embedding",
                limit=top_k,
                output_fields=["text", "filename"],
                filter=filter_expr
            )
            
            similar_texts = []
            for hits in results:
                for hit in hits:
                    # 调试：打印原始结果格式
                    print(f"Debug - 原始搜索结果: {hit}")
                    
                    # 尝试不同的方式提取 score
                    score = 0.0
                    
                    # 方法1: 直接获取 score
                    if "score" in hit:
                        score = float(hit["score"])
                    # 方法2: 获取 distance 并转换为相似度
                    elif "distance" in hit:
                        score = 1.0 - float(hit["distance"])
                    # 方法3: 检查是否有其他相似度字段
                    elif "similarity" in hit:
                        score = float(hit["similarity"])
                    # 方法4: 如果是列表格式，可能 score 在特定位置
                    elif isinstance(hit, (list, tuple)) and len(hit) > 1:
                        score = float(hit[1]) if isinstance(hit[1], (int, float)) else 0.0
                    else:
                        # 如果没有找到分数，使用默认值
                        score = 0.5  # 使用默认相似度
                    
                    similar_texts.append({
                        "text": hit.get("text", ""),
                        "filename": hit.get("filename", ""),
                        "score": score,
                        "id": hit.get("id", 0)
                    })
            
            return similar_texts
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
    
    def search_by_filename(self, filename: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """按文件名搜索文档内容"""
        try:
            # 查询指定文件的所有文本
            results = self.milvus_client.query(
                collection_name=self.collection_name,
                filter=f'filename == "{filename}"',
                output_fields=["text", "filename"],
                limit=top_k
            )
            
            return results
        except Exception as e:
            print(f"按文件名搜索失败: {e}")
            return []
    
    def get_available_files(self) -> List[str]:
        """获取可用的文件列表"""
        try:
            # 查询所有文件名
            results = self.milvus_client.query(
                collection_name=self.collection_name,
                filter="",
                output_fields=["filename"],
                limit=1000  # 添加 limit 参数
            )
            
            # 去重
            files = list(set([result.get("filename") for result in results if result.get("filename")]))
            return files
        except Exception as e:
            print(f"获取文件列表失败: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        try:
            collections = self.milvus_client.list_collections()
            files = self.get_available_files()
            
            # 获取集合统计信息
            stats = self.milvus_client.get_collection_stats(self.collection_name)
            
            return {
                "collection_name": self.collection_name,
                "num_entities": stats.get("row_count", 0),
                "available_files": files,
                "processed_files_count": len(self.processed_files),
                "db_path": os.path.join(self.db_data_dir, "milvus_lite.db"),
                "stats": stats
            }
        except Exception as e:
            print(f"获取集合信息失败: {e}")
            return {}
