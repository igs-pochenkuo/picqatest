"""
資料管理器模組
負責處理結果資料的儲存、載入和匯出
"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import csv

from config import config
from utils import (
    save_results_to_json, 
    load_results_from_json, 
    create_timestamp_filename,
    calculate_statistics
)

class DataManager:
    """資料管理器"""
    
    def __init__(self):
        """初始化資料管理器"""
        self.results_dir = config.get('export.results_dir', 'data/results')
        self.exports_dir = config.get('export.exports_dir', 'data/exports')
        
        # 確保目錄存在
        Path(self.results_dir).mkdir(parents=True, exist_ok=True)
        Path(self.exports_dir).mkdir(parents=True, exist_ok=True)
    
    def save_analysis_results(self, results: List[Dict[str, Any]], 
                            prompt: str, folder_path: str,
                            model_info: Dict[str, Any]) -> str:
        """
        儲存分析結果
        
        Args:
            results (List[Dict[str, Any]]): 分析結果列表
            prompt (str): 使用的文字提示
            folder_path (str): 分析的資料夾路徑
            model_info (Dict[str, Any]): 模型資訊
            
        Returns:
            str: 儲存的檔案路徑
        """
        # 準備完整的結果資料
        analysis_data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'prompt': prompt,
                'folder_path': folder_path,
                'total_images': len(results),
                'successful_analyses': sum(1 for r in results if r.get('success', False)),
                'model_info': model_info
            },
            'results': results,
            'statistics': self._calculate_result_statistics(results)
        }
        
        # 生成檔案名稱
        filename = create_timestamp_filename('analysis_results', 'json')
        file_path = Path(self.results_dir) / filename
        
        # 儲存結果
        if save_results_to_json(analysis_data, str(file_path)):
            print(f"分析結果已儲存至: {file_path}")
            return str(file_path)
        else:
            print("儲存分析結果失敗")
            return ""
    
    def load_analysis_results(self, file_path: str) -> Dict[str, Any]:
        """
        載入分析結果
        
        Args:
            file_path (str): 結果檔案路徑
            
        Returns:
            Dict[str, Any]: 分析結果資料
        """
        return load_results_from_json(file_path)
    
    def export_to_csv(self, results: List[Dict[str, Any]], 
                     output_filename: Optional[str] = None) -> str:
        """
        匯出結果為 CSV 格式
        
        Args:
            results (List[Dict[str, Any]]): 結果列表
            output_filename (str, optional): 輸出檔案名稱
            
        Returns:
            str: 匯出檔案路徑
        """
        if not results:
            print("沒有結果可以匯出")
            return ""
        
        # 生成檔案名稱
        if output_filename is None:
            output_filename = create_timestamp_filename('similarity_results', 'csv')
        
        file_path = Path(self.exports_dir) / output_filename
        
        try:
            # 準備 CSV 資料
            csv_data = []
            for result in results:
                csv_row = {
                    '圖片路徑': result.get('image_path', ''),
                    '圖片名稱': result.get('image_name', ''),
                    'Prompt': result.get('prompt', ''),
                    '相似度分數': result.get('similarity_score', 0.0),
                    '處理成功': result.get('success', False),
                    '錯誤訊息': result.get('error', '')
                }
                csv_data.append(csv_row)
            
            # 寫入 CSV 檔案
            df = pd.DataFrame(csv_data)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            print(f"CSV 檔案已匯出至: {file_path}")
            return str(file_path)
            
        except Exception as e:
            print(f"匯出 CSV 檔案時發生錯誤: {e}")
            return ""
    
    def export_filtered_results(self, results: List[Dict[str, Any]], 
                              similarity_threshold: float,
                              output_filename: Optional[str] = None) -> str:
        """
        匯出過濾後的結果
        
        Args:
            results (List[Dict[str, Any]]): 原始結果列表
            similarity_threshold (float): 相似度閾值
            output_filename (str, optional): 輸出檔案名稱
            
        Returns:
            str: 匯出檔案路徑
        """
        # 過濾結果
        filtered_results = [
            result for result in results
            if result.get('success', False) and 
               result.get('similarity_score', 0) >= similarity_threshold
        ]
        
        if not filtered_results:
            print(f"沒有符合閾值 {similarity_threshold} 的結果")
            return ""
        
        # 生成檔案名稱
        if output_filename is None:
            threshold_str = f"{similarity_threshold:.2f}".replace('.', '_')
            output_filename = create_timestamp_filename(f'filtered_results_threshold_{threshold_str}', 'csv')
        
        return self.export_to_csv(filtered_results, output_filename)
    
    def get_recent_results(self, limit: int = 10) -> List[Dict[str, str]]:
        """
        取得最近的分析結果檔案
        
        Args:
            limit (int): 返回檔案數量限制
            
        Returns:
            List[Dict[str, str]]: 檔案資訊列表
        """
        results_path = Path(self.results_dir)
        
        if not results_path.exists():
            return []
        
        # 取得所有 JSON 檔案
        json_files = list(results_path.glob('*.json'))
        
        # 按修改時間排序
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # 限制數量
        json_files = json_files[:limit]
        
        # 準備檔案資訊
        file_info = []
        for file_path in json_files:
            try:
                # 載入基本資訊
                data = load_results_from_json(str(file_path))
                metadata = data.get('metadata', {})
                
                info = {
                    'file_path': str(file_path),
                    'filename': file_path.name,
                    'timestamp': metadata.get('timestamp', ''),
                    'prompt': metadata.get('prompt', ''),
                    'total_images': metadata.get('total_images', 0),
                    'successful_analyses': metadata.get('successful_analyses', 0),
                    'file_size_mb': file_path.stat().st_size / (1024 * 1024)
                }
                file_info.append(info)
                
            except Exception as e:
                print(f"讀取檔案 {file_path} 資訊時發生錯誤: {e}")
        
        return file_info
    
    def _calculate_result_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        計算結果統計資料
        
        Args:
            results (List[Dict[str, Any]]): 結果列表
            
        Returns:
            Dict[str, Any]: 統計資料
        """
        if not results:
            return {}
        
        # 取得成功的相似度分數
        similarity_scores = [
            result['similarity_score'] 
            for result in results 
            if result.get('success', False) and result.get('similarity_score') is not None
        ]
        
        # 計算基本統計
        stats = calculate_statistics(similarity_scores)
        
        # 添加額外統計資訊
        stats.update({
            'total_images': len(results),
            'successful_analyses': len(similarity_scores),
            'failed_analyses': len(results) - len(similarity_scores),
            'success_rate': len(similarity_scores) / len(results) if results else 0.0
        })
        
        # 計算不同閾值下的通過率
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        threshold_stats = {}
        
        for threshold in thresholds:
            passed_count = sum(1 for score in similarity_scores if score >= threshold)
            threshold_stats[f'threshold_{threshold:.1f}'] = {
                'count': passed_count,
                'percentage': passed_count / len(similarity_scores) if similarity_scores else 0.0
            }
        
        stats['threshold_analysis'] = threshold_stats
        
        return stats
    
    def create_summary_report(self, results: List[Dict[str, Any]], 
                            prompt: str, folder_path: str) -> str:
        """
        創建摘要報告
        
        Args:
            results (List[Dict[str, Any]]): 結果列表
            prompt (str): 使用的文字提示
            folder_path (str): 分析的資料夾路徑
            
        Returns:
            str: 摘要報告文字
        """
        stats = self._calculate_result_statistics(results)
        
        report = f"""
=== PictureQA 分析摘要報告 ===

分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
資料夾路徑: {folder_path}
使用的 Prompt: "{prompt}"

=== 處理統計 ===
總圖片數: {stats.get('total_images', 0)}
成功分析: {stats.get('successful_analyses', 0)}
失敗分析: {stats.get('failed_analyses', 0)}
成功率: {stats.get('success_rate', 0):.2%}

=== 相似度統計 ===
平均相似度: {stats.get('mean', 0):.4f}
中位數相似度: {stats.get('median', 0):.4f}
最高相似度: {stats.get('max', 0):.4f}
最低相似度: {stats.get('min', 0):.4f}
標準差: {stats.get('std', 0):.4f}

=== 不同閾值通過統計 ===
"""
        
        # 添加閾值統計
        threshold_analysis = stats.get('threshold_analysis', {})
        for threshold_key, threshold_data in threshold_analysis.items():
            threshold_value = threshold_key.replace('threshold_', '')
            count = threshold_data.get('count', 0)
            percentage = threshold_data.get('percentage', 0)
            report += f"閾值 {threshold_value}: {count} 張圖片 ({percentage:.1%})\n"
        
        return report
    
    def cleanup_old_files(self, days_to_keep: int = 30):
        """
        清理舊檔案
        
        Args:
            days_to_keep (int): 保留天數
        """
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)
        
        # 清理結果檔案
        results_path = Path(self.results_dir)
        if results_path.exists():
            for file_path in results_path.glob('*.json'):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    print(f"已刪除舊檔案: {file_path}")
        
        # 清理匯出檔案
        exports_path = Path(self.exports_dir)
        if exports_path.exists():
            for file_path in exports_path.glob('*.csv'):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    print(f"已刪除舊檔案: {file_path}") 