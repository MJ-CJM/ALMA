import os
import PyPDF2
from pymilvus import MilvusClient
import re
from typing import List, Dict, Any
import uuid
import psutil
import gc
import time
import requests
import json
from openai import OpenAI

class RAGService:
    def __init__(self, 
                 pdf_dir: str = "../data/pdf",
                 milvus_db_file: str = "db_data/milvus_lite.db",
                 collection_name: str = "pdf_documents",
                 api_key: str = "sk-1f0b08f7ee4742c39dbb63254f3db29e",
                 base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
                 embedding_model: str = "text-embedding-v4",
                 embedding_dimension: int = 1024):
        self.pdf_dir = pdf_dir
        self.milvus_db_file = milvus_db_file
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension
        
        # 初始化OpenAI客户端
        self.api_key = api_key or os.getenv("ALIYUN_API_KEY")
        if not self.api_key:
            raise ValueError("请设置ALIYUN_API_KEY环境变量或传入api_key参数")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url
        )
        
        self._init_milvus()
    
    def _check_memory_and_wait(self, threshold: float = 75.0):
        """检查内存并在必要时等待"""
        memory = psutil.virtual_memory()
        if memory.percent > threshold:
            print(f"内存使用率 {memory.percent:.1f}% 超过阈值，等待释放...")
            gc.collect()
            time.sleep(2)
            return True
        return False
    
    def _check_memory(self, threshold: float = 80.0) -> bool:
        """检查内存使用率，超过阈值时返回True"""
        memory = psutil.virtual_memory()
        if memory.percent > threshold:
            print(f"警告: 内存使用率 {memory.percent:.1f}% 超过阈值 {threshold}%")
            return True
        return False
    
    def _init_milvus(self):
        """初始化Milvus Lite连接"""
        import time
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.milvus_db_file), exist_ok=True)
        
        # 重试连接机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 使用 Milvus Lite 客户端
                self.milvus_client = MilvusClient(uri=self.milvus_db_file)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"数据库连接失败，尝试重试 {attempt + 1}/{max_retries}...")
                    time.sleep(2)
                    continue
                else:
                    # 最后一次尝试：删除锁定的数据库文件
                    try:
                        if os.path.exists(self.milvus_db_file):
                            os.remove(self.milvus_db_file)
                            print(f"已删除锁定的数据库文件: {self.milvus_db_file}")
                    except:
                        pass
                    # 重新创建连接
                    self.milvus_client = MilvusClient(uri=self.milvus_db_file)
        
        # 如果集合存在，删除它
        try:
            if self.milvus_client.has_collection(self.collection_name):
                self.milvus_client.drop_collection(self.collection_name)
        except:
            pass
        
        # 创建集合 - 使用API模型的维度
        self.milvus_client.create_collection(
            collection_name=self.collection_name,
            dimension=self.embedding_dimension,  # 使用API模型的维度
            metric_type="L2",
            consistency_level="Strong"
        )
        print(f"Milvus集合创建成功，维度: {self.embedding_dimension}")
    
    def _get_embeddings_api(self, texts: List[str]) -> List[List[float]]:
        """通过API获取文本嵌入向量"""
        try:
            # 检查输入长度限制
            processed_texts = []
            for text in texts:
                # 限制每个文本的长度（大约8000个字符，保守估计）
                if len(text) > 8000:
                    text = text[:8000]
                processed_texts.append(text)
            
            # 确保列表长度不超过10个
            if len(processed_texts) > 10:
                processed_texts = processed_texts[:10]
            
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=processed_texts,
                dimensions=self.embedding_dimension,
                encoding_format="float"
            )
            
            # 提取向量数据
            embeddings = []
            for embedding_data in response.data:
                embeddings.append(embedding_data.embedding)
            
            return embeddings
            
        except Exception as e:
            print(f"API调用失败: {e}")
            # 返回零向量作为备用
            return [[0.0] * self.embedding_dimension] * len(texts)
    
    def extract_text_from_pdf_streaming(self, pdf_path: str):
        """流式从PDF提取文本，逐页处理避免内存峰值"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                print(f"  - PDF共 {total_pages} 页，开始逐页处理...")
                
                for page_num in range(total_pages):
                    try:
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text()
                        
                        if page_text.strip():  # 只处理非空页面
                            yield page_text, page_num + 1, total_pages
                        
                        # 立即清理页面对象
                        del page, page_text
                        gc.collect()
                        
                    except Exception as e:
                        print(f"    警告: 第{page_num + 1}页提取失败: {e}")
                        continue
        except Exception as e:
            print(f"PDF文件读取失败: {e}")
            return
    
    def split_text_into_chunks(self, text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
        """将文本分割成固定大小的块"""
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            if end > text_len:
                end = text_len
            
            # 尝试在句子结束处分割
            if end < text_len:
                # 查找最近的句号、问号或感叹号
                for i in range(end, max(start + chunk_size//2, start), -1):
                    if text[i] in '.!?。！？':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if len(chunk) > 30:  # 降低最小长度阈值
                chunks.append(chunk)
            
            start = end - overlap  # 重叠部分避免丢失上下文
            if start < 0:
                start = 0
        
        return chunks
    
    def process_pdfs(self, batch_size: int = 5):  # API版本可以使用更大的批次
        """处理PDF文件并建立索引 - 使用API版本"""
        import time
        
        if not os.path.exists(self.pdf_dir):
            os.makedirs(self.pdf_dir)
            return
        
        # 内存预检查
        initial_memory = psutil.virtual_memory()
        print(f"开始处理前内存使用: {initial_memory.percent:.1f}%")
        
        if initial_memory.percent > 70:
            print("警告：系统内存使用已较高，建议先释放内存")
            
        pdf_files = [f for f in os.listdir(self.pdf_dir) if f.endswith('.pdf')]
        print(f"找到 {len(pdf_files)} 个PDF文件")
        
        doc_id = 0
        total_chunks = 0
        
        for pdf_file in pdf_files:
            print(f"正在处理: {pdf_file}")
            pdf_path = os.path.join(self.pdf_dir, pdf_file)
            
            try:
                processed_pages = 0
                text_batch = []
                id_batch = []
                filename_batch = []
                
                # 流式处理每一页
                for page_text, page_num, total_pages in self.extract_text_from_pdf_streaming(pdf_path):
                    processed_pages += 1
                    
                    # 检查内存状态
                    if processed_pages % 3 == 0:  # 每3页检查一次
                        memory = psutil.virtual_memory()
                        print(f"    第{page_num}/{total_pages}页, 内存: {memory.percent:.1f}%")
                        
                        if memory.percent > 80:
                            print("    内存使用过高，暂停处理...")
                            gc.collect()
                            time.sleep(1)
                    
                    # 分割页面文本为小块
                    page_chunks = self.split_text_into_chunks(page_text, chunk_size=400, overlap=50)
                    
                    for chunk in page_chunks:
                        if len(chunk) > 30:  # 降低最小长度阈值
                            try:
                                # 检查内存
                                self._check_memory_and_wait(75.0)
                                
                                # 添加到批次
                                text_batch.append(chunk)
                                id_batch.append(doc_id)
                                filename_batch.append(pdf_file)
                                doc_id += 1
                                
                                # 当批次达到指定大小时，调用API
                                if len(text_batch) >= batch_size:
                                    # 获取嵌入向量
                                    embeddings = self._get_embeddings_api(text_batch)
                                    
                                    # 插入到数据库
                                    for i, embedding in enumerate(embeddings):
                                        self.milvus_client.insert(collection_name=self.collection_name, data=[{
                                            "id": id_batch[i],
                                            "text": text_batch[i],
                                            "filename": filename_batch[i],
                                            "vector": embedding
                                        }])
                                    
                                    total_chunks += len(text_batch)
                                    print(f"    已处理 {len(text_batch)} 个片段 (总计: {total_chunks})")
                                    
                                    # 清理批次
                                    text_batch = []
                                    id_batch = []
                                    filename_batch = []
                                    
                                    # 清理内存
                                    del embeddings
                                    gc.collect()
                                    
                                    # 如果内存使用过高，强制暂停
                                    memory = psutil.virtual_memory()
                                    if memory.percent > 80:
                                        print("    内存压力大，暂停1秒...")
                                        time.sleep(1)
                                        gc.collect()
                                        
                            except Exception as e:
                                print(f"    处理chunk时出错: {e}")
                                continue
                    
                    # 每页处理完清理页面数据
                    del page_text, page_chunks
                    gc.collect()
                
                # 处理剩余的批次
                if text_batch:
                    try:
                        embeddings = self._get_embeddings_api(text_batch)
                        
                        for i, embedding in enumerate(embeddings):
                            self.milvus_client.insert(collection_name=self.collection_name, data=[{
                                "id": id_batch[i],
                                "text": text_batch[i],
                                "filename": filename_batch[i],
                                "vector": embedding
                            }])
                        
                        total_chunks += len(text_batch)
                        print(f"  - 处理最后 {len(text_batch)} 个片段 (总计: {total_chunks})")
                        
                    except Exception as e:
                        print(f"处理最后批次时出错: {e}")
                
                print(f"  - {pdf_file} 处理完成，共处理 {processed_pages} 页")
                
            except Exception as e:
                print(f"处理 {pdf_file} 时出错: {e}")
                import traceback
                traceback.print_exc()
                continue
            finally:
                # 强制清理
                gc.collect()
        
        final_memory = psutil.virtual_memory()
        print(f"处理完成！总共索引了 {total_chunks} 个文本片段")
        print(f"最终内存使用: {final_memory.percent:.1f}%")
    
    def search(self, query: str, limit: int = 5, score_threshold: float = None) -> List[Dict[str, Any]]:
        """搜索相关文档"""
        if not query:
            return []
        
        try:
            # 获取查询的嵌入向量
            query_embeddings = self._get_embeddings_api([query])
            if not query_embeddings:
                return []
            
            query_embedding = query_embeddings[0]
            
            results = self.milvus_client.search(
                collection_name=self.collection_name,
                data=[query_embedding],
                limit=limit,
                output_fields=["text", "filename"]
            )
            
            search_results = []
            for hit in results[0]:
                score = hit.get('distance', 0.0)
                # 如果设置了阈值，过滤低相关性结果
                if score_threshold is not None and score > score_threshold:
                    continue
                    
                search_results.append({
                    'text': hit.get('entity', {}).get('text', ''),
                    'filename': hit.get('entity', {}).get('filename', ''),
                    'score': score,
                    'text_length': len(hit.get('entity', {}).get('text', ''))
                })
            
            return search_results
        
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            stats = self.milvus_client.get_collection_stats(self.collection_name)
            return {
                "total_documents": stats.get("row_count", 0),
                "collection_name": self.collection_name,
                "status": "ready"
            }
        except Exception as e:
            return {
                "total_documents": 0,
                "collection_name": self.collection_name,
                "status": "error",
                "error": str(e)
            } 