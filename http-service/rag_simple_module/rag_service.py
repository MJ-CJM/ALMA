import os
import fitz  # PyMuPDF
from typing import List, Dict, Any
from openai import OpenAI
from pymilvus import MilvusClient
import hashlib

class RAGService:
    """简化的 RAG 服务"""
    
    def __init__(self):
        # 初始化 OpenAI 客户端用于 embedding
        self.client = OpenAI(
            api_key="sk-1f0b08f7ee4742c39dbb63254f3db29e",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # Milvus 连接配置
        self.collection_name = "rag_simple_collection"
        self.dim = 1536  # embedding 维度
        
        # 连接 Milvus
        self._connect_milvus()
        self._create_collection()
        
        # 自动加载 PDF 文件
        self.auto_load_pdf_files()
    
    def _connect_milvus(self):
        """连接远程 Milvus 服务器"""
        try:
            self.milvus_client = MilvusClient(
                uri="http://101.34.214.7:6002"
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
                print(f"集合 {self.collection_name} 已存在，正在删除...")
                self.milvus_client.drop_collection(self.collection_name)
            
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
        """获取文件哈希值"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def auto_load_pdf_files(self, pdf_dir: str = "data/pdf"):
        """自动加载 PDF 文件"""
        if not os.path.exists(pdf_dir):
            print(f"PDF 目录不存在: {pdf_dir}")
            return
        
        pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
        if not pdf_files:
            print(f"在 {pdf_dir} 中未找到 PDF 文件")
            return
        
        print(f"找到 {len(pdf_files)} 个 PDF 文件")
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(pdf_dir, pdf_file)
            self.process_pdf_file(pdf_path)
    
    def process_pdf_file(self, pdf_path: str):
        """处理单个 PDF 文件"""
        try:
            print(f"处理 PDF 文件: {pdf_path}")
            
            # 提取文本段落
            text_segments = self.extract_text_from_pdf(pdf_path)
            if not text_segments:
                print(f"从 {pdf_path} 中未提取到文本")
                return
            
            # 生成 embedding
            embeddings = self.get_embeddings(text_segments)
            
            # 准备数据
            data = []
            for i, (text, emb) in enumerate(zip(text_segments, embeddings)):
                data.append({
                    "id": len(data) + 1,
                    "text": text,
                    "embedding": emb,
                    "filename": os.path.basename(pdf_path),
                    "file_hash": self._get_file_hash(pdf_path)
                })
            
            # 插入到 Milvus
            self.milvus_client.insert(
                collection_name=self.collection_name,
                data=data
            )
            
            # 刷新集合
            self.milvus_client.flush(collection_name=self.collection_name)
            print(f"成功插入 {len(data)} 条数据")
            
        except Exception as e:
            print(f"处理 PDF 文件 {pdf_path} 时出错: {e}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[str]:
        """从 PDF 文件中提取文本段落"""
        try:
            doc = fitz.open(pdf_path)
            text_segments = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                # 按固定长度分割文本
                chunk_size = 500
                for i in range(0, len(text), chunk_size):
                    chunk = text[i:i + chunk_size].strip()
                    if len(chunk) > 50:  # 至少50个字符
                        text_segments.append(chunk)
            
            doc.close()
            print(f"提取了 {len(text_segments)} 个文本段落")
            
            # 调试：显示前几个段落的长度
            for i, segment in enumerate(text_segments[:5]):
                print(f"段落 {i+1}: {len(segment)} 字符")
            
            return text_segments
            
        except Exception as e:
            print(f"提取 PDF 文本时出错: {e}")
            return []
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """获取文本的 embedding"""
        try:
            # 过滤掉空文本和过长的文本
            valid_texts = []
            for i, text in enumerate(texts):
                text_len = len(text.strip())
                if text.strip() and text_len <= 500:
                    valid_texts.append(text.strip())
                    print(f"文本段落 {i+1}: {text_len} 字符")
                elif text.strip():
                    print(f"跳过过长的文本段落 {i+1}: {text_len} 字符")
            
            if not valid_texts:
                print("没有有效的文本用于生成 embedding")
                return []
            
            print(f"为 {len(valid_texts)} 个文本段落生成 embedding...")
            
            # 分批处理，每批最多25个
            batch_size = 25
            all_embeddings = []
            
            for i in range(0, len(valid_texts), batch_size):
                batch = valid_texts[i:i + batch_size]
                print(f"处理批次 {i//batch_size + 1}: {len(batch)} 个文本")
                
                response = self.client.embeddings.create(
                    input=batch,
                    model="text-embedding-v1"
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
        except Exception as e:
            print(f"生成 embedding 时出错: {e}")
            return []
    
    def search_similar_texts(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似文本"""
        try:
            # 生成查询的 embedding
            response = self.client.embeddings.create(
                input=[query],
                model="text-embedding-v1"
            )
            query_embedding = response.data[0].embedding
            
            # 搜索相似文本
            results = self.milvus_client.search(
                collection_name=self.collection_name,
                data=[query_embedding],
                limit=top_k,
                output_fields=["id", "text", "filename"]
            )
            
            # 格式化结果
            formatted_results = []
            if results and len(results) > 0:
                for hit in results[0]:
                    formatted_results.append({
                        "id": hit.get("id"),
                        "content": hit.get("text", ""),
                        "filename": hit.get("filename", ""),
                        "score": hit.get("score", 0)
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"搜索相似文本时出错: {e}")
            return [] 