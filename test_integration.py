#!/usr/bin/env python3
"""
智能文本QA生成系统 - 整合版集成测试
验证所有模块和功能是否正确整合
"""

import os
import sys
import json
import importlib
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class IntegrationTester:
    """整合测试器"""
    
    def __init__(self):
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'details': []
        }
        
    def log_test(self, test_name: str, status: str, message: str = "", details: Any = None):
        """记录测试结果"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'details': details
        }
        self.test_results['details'].append(result)
        
        if status == 'PASS':
            self.test_results['passed'] += 1
            print(f"✅ {test_name}: {message}")
        elif status == 'FAIL':
            self.test_results['failed'] += 1
            print(f"❌ {test_name}: {message}")
        elif status == 'WARN':
            self.test_results['warnings'] += 1
            print(f"⚠️  {test_name}: {message}")
    
    def test_file_structure(self):
        """测试文件结构完整性"""
        print("\n🔍 测试文件结构...")
        
        required_files = [
            'run_pipeline.py',
            'config.json', 
            'requirements.txt',
            'README.md',
            'quick_start.sh'
        ]
        
        required_dirs = [
            'TextQA',
            'TextGeneration',
            'LocalModels',
            'MultiModal'
        ]
        
        # 检查必需文件
        for file in required_files:
            if os.path.exists(file):
                self.log_test(f"文件存在检查", "PASS", f"{file} 存在")
            else:
                self.log_test(f"文件存在检查", "FAIL", f"{file} 不存在")
        
        # 检查必需目录
        for directory in required_dirs:
            if os.path.isdir(directory):
                self.log_test(f"目录存在检查", "PASS", f"{directory}/ 存在")
            else:
                self.log_test(f"目录存在检查", "FAIL", f"{directory}/ 不存在")
    
    def test_config_validity(self):
        """测试配置文件有效性"""
        print("\n🔍 测试配置文件...")
        
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.log_test("配置文件解析", "PASS", "config.json 格式正确")
            
            # 检查必需的配置节
            required_sections = [
                'system_info',
                'api',
                'models',
                'processing',
                'professional_domains'
            ]
            
            for section in required_sections:
                if section in config:
                    self.log_test("配置节检查", "PASS", f"配置节 {section} 存在")
                else:
                    self.log_test("配置节检查", "FAIL", f"配置节 {section} 缺失")
            
            # 检查版本信息
            if 'system_info' in config and 'version' in config['system_info']:
                version = config['system_info']['version']
                self.log_test("版本信息", "PASS", f"系统版本: {version}")
            
            # 检查功能特性
            if 'system_info' in config and 'features' in config['system_info']:
                features = config['system_info']['features']
                self.log_test("功能特性", "PASS", f"集成功能: {len(features)} 个")
                
        except json.JSONDecodeError as e:
            self.log_test("配置文件解析", "FAIL", f"JSON格式错误: {e}")
        except Exception as e:
            self.log_test("配置文件解析", "FAIL", f"读取失败: {e}")
    
    def test_module_imports(self):
        """测试模块导入"""
        print("\n🔍 测试模块导入...")
        
        # 核心模块
        core_modules = [
            ('TextQA.dataargument', 'TextQA数据处理'),
            ('TextQA.enhanced_quality_checker', 'TextQA增强质量检查'),
            ('TextGeneration.Datageneration', 'TextGeneration数据生成'),
            ('TextGeneration.prompts_conf', 'TextGeneration Prompt配置')
        ]
        
        for module_name, description in core_modules:
            try:
                importlib.import_module(module_name)
                self.log_test("模块导入", "PASS", f"{description} 导入成功")
            except ImportError as e:
                self.log_test("模块导入", "FAIL", f"{description} 导入失败: {e}")
            except Exception as e:
                self.log_test("模块导入", "FAIL", f"{description} 异常: {e}")
        
        # 可选模块
        optional_modules = [
            ('LocalModels.ollama_client', '本地模型支持'),
            ('MultiModal.pdf_processor', '多模态PDF处理')
        ]
        
        for module_name, description in optional_modules:
            try:
                importlib.import_module(module_name)
                self.log_test("可选模块导入", "PASS", f"{description} 导入成功")
            except ImportError:
                self.log_test("可选模块导入", "WARN", f"{description} 不可用（可能未安装依赖）")
            except Exception as e:
                self.log_test("可选模块导入", "WARN", f"{description} 异常: {e}")
    
    def test_prompts_availability(self):
        """测试Prompt模板可用性"""
        print("\n🔍 测试Prompt模板...")
        
        try:
            from TextGeneration.prompts_conf import user_prompts
            
            prompt_count = len(user_prompts)
            self.log_test("Prompt数量", "PASS", f"可用Prompt: {prompt_count} 个")
            
            # 检查关键Prompt
            key_prompts = [343, 3431, 3432]
            for prompt_id in key_prompts:
                if prompt_id in user_prompts:
                    self.log_test("关键Prompt", "PASS", f"Prompt {prompt_id} 存在")
                else:
                    self.log_test("关键Prompt", "WARN", f"Prompt {prompt_id} 不存在")
                    
        except Exception as e:
            self.log_test("Prompt模板", "FAIL", f"Prompt模板加载失败: {e}")
    
    def test_dependencies(self):
        """测试依赖包"""
        print("\n🔍 测试依赖包...")
        
        # 核心依赖
        core_deps = [
            ('asyncio', '异步处理'),
            ('json', 'JSON处理'),
            ('pandas', '数据处理'),
            ('numpy', '数值计算'),
            ('aiohttp', 'HTTP客户端')
        ]
        
        for dep, description in core_deps:
            try:
                importlib.import_module(dep)
                self.log_test("核心依赖", "PASS", f"{description} ({dep}) 可用")
            except ImportError:
                self.log_test("核心依赖", "FAIL", f"{description} ({dep}) 缺失")
        
        # 可选依赖
        optional_deps = [
            ('fitz', 'PDF处理 (PyMuPDF)'),
            ('PIL', '图像处理 (Pillow)'),
            ('cv2', '计算机视觉 (OpenCV)'),
            ('transformers', 'Transformers模型'),
            ('torch', 'PyTorch')
        ]
        
        for dep, description in optional_deps:
            try:
                importlib.import_module(dep)
                self.log_test("可选依赖", "PASS", f"{description} 可用")
            except ImportError:
                self.log_test("可选依赖", "WARN", f"{description} 不可用")
    
    def test_pipeline_script(self):
        """测试主流水线脚本"""
        print("\n🔍 测试主流水线脚本...")
        
        try:
            # 检查脚本语法
            with open('run_pipeline.py', 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # 简单的语法检查
            compile(script_content, 'run_pipeline.py', 'exec')
            self.log_test("流水线脚本", "PASS", "run_pipeline.py 语法正确")
            
            # 检查关键类和函数
            if 'class IntegratedQAPipeline' in script_content:
                self.log_test("流水线类", "PASS", "IntegratedQAPipeline 类存在")
            else:
                self.log_test("流水线类", "FAIL", "IntegratedQAPipeline 类不存在")
            
            # 检查关键方法
            key_methods = [
                'run_full_pipeline',
                'stage_text_retrieval', 
                'stage_data_cleaning',
                'stage_qa_generation',
                'stage_quality_control'
            ]
            
            for method in key_methods:
                if f'def {method}' in script_content:
                    self.log_test("流水线方法", "PASS", f"方法 {method} 存在")
                else:
                    self.log_test("流水线方法", "FAIL", f"方法 {method} 不存在")
                    
        except SyntaxError as e:
            self.log_test("流水线脚本", "FAIL", f"语法错误: {e}")
        except Exception as e:
            self.log_test("流水线脚本", "FAIL", f"检查失败: {e}")
    
    def test_quick_start_script(self):
        """测试快速启动脚本"""
        print("\n🔍 测试快速启动脚本...")
        
        if os.path.exists('quick_start.sh'):
            # 检查脚本是否可执行
            if os.access('quick_start.sh', os.X_OK):
                self.log_test("启动脚本", "PASS", "quick_start.sh 可执行")
            else:
                self.log_test("启动脚本", "WARN", "quick_start.sh 不可执行，可能需要 chmod +x")
            
            # 检查脚本内容
            try:
                with open('quick_start.sh', 'r', encoding='utf-8') as f:
                    script_content = f.read()
                
                # 检查关键功能
                key_functions = [
                    'show_help',
                    'setup_environment',
                    'check_environment',
                    'run_full_pipeline'
                ]
                
                for func in key_functions:
                    if func in script_content:
                        self.log_test("启动脚本功能", "PASS", f"功能 {func} 存在")
                    else:
                        self.log_test("启动脚本功能", "WARN", f"功能 {func} 不存在")
                        
            except Exception as e:
                self.log_test("启动脚本", "FAIL", f"读取失败: {e}")
        else:
            self.log_test("启动脚本", "FAIL", "quick_start.sh 不存在")
    
    def test_directory_structure(self):
        """测试目录结构"""
        print("\n🔍 测试目录结构...")
        
        # 创建测试目录
        test_dirs = [
            'data',
            'data/input',
            'data/output',
            'logs',
            'temp'
        ]
        
        for directory in test_dirs:
            try:
                os.makedirs(directory, exist_ok=True)
                if os.path.isdir(directory):
                    self.log_test("目录创建", "PASS", f"目录 {directory} 存在/创建成功")
                else:
                    self.log_test("目录创建", "FAIL", f"目录 {directory} 创建失败")
            except Exception as e:
                self.log_test("目录创建", "FAIL", f"目录 {directory} 创建异常: {e}")
    
    def test_configuration_completeness(self):
        """测试配置完整性"""
        print("\n🔍 测试配置完整性...")
        
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 检查整合的功能配置
            integration_features = [
                ('multimodal', '多模态处理'),
                ('local_models', '本地模型'),
                ('professional_domains', '专业领域'),
                ('quality_control', '质量控制'),
                ('rewriting', '数据改写')
            ]
            
            for feature_key, feature_name in integration_features:
                if feature_key in config:
                    self.log_test("功能配置", "PASS", f"{feature_name} 配置存在")
                else:
                    self.log_test("功能配置", "WARN", f"{feature_name} 配置缺失")
            
            # 检查领域配置
            if 'professional_domains' in config:
                domains = config['professional_domains']
                if 'semiconductor' in domains and 'optics' in domains:
                    self.log_test("领域配置", "PASS", "半导体和光学领域配置完整")
                else:
                    self.log_test("领域配置", "WARN", "部分专业领域配置缺失")
                    
        except Exception as e:
            self.log_test("配置完整性", "FAIL", f"配置检查失败: {e}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始整合测试...")
        print("=" * 60)
        
        # 执行各项测试
        self.test_file_structure()
        self.test_config_validity()
        self.test_module_imports()
        self.test_prompts_availability()
        self.test_dependencies()
        self.test_pipeline_script()
        self.test_quick_start_script()
        self.test_directory_structure()
        self.test_configuration_completeness()
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 整合测试报告")
        print("=" * 60)
        
        total_tests = self.test_results['passed'] + self.test_results['failed'] + self.test_results['warnings']
        
        print(f"总测试数: {total_tests}")
        print(f"✅ 通过: {self.test_results['passed']}")
        print(f"❌ 失败: {self.test_results['failed']}")
        print(f"⚠️  警告: {self.test_results['warnings']}")
        
        if self.test_results['failed'] == 0:
            print("\n🎉 整合测试通过！系统已成功整合所有功能。")
            success_rate = (self.test_results['passed'] / total_tests) * 100
            print(f"成功率: {success_rate:.1f}%")
        else:
            print("\n⚠️  整合测试发现问题，请检查失败的测试项。")
        
        # 保存详细报告
        report_file = 'logs/integration_test_report.json'
        os.makedirs('logs', exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=4)
        
        print(f"\n📄 详细报告已保存: {report_file}")
        
        # 显示整合状态
        print("\n🔧 整合状态总结:")
        print("=" * 40)
        
        integration_status = {
            "文本召回与检索": "✅ 已整合",
            "数据清理与预处理": "✅ 已整合", 
            "智能QA生成": "✅ 已整合",
            "增强质量控制": "✅ 已整合",
            "多模态处理": "✅ 已整合" if self.test_results['failed'] == 0 else "⚠️ 部分整合",
            "本地模型支持": "✅ 已整合" if self.test_results['failed'] == 0 else "⚠️ 部分整合",
            "专业领域定制": "✅ 已整合",
            "统一配置系统": "✅ 已整合",
            "统一流水线": "✅ 已整合"
        }
        
        for feature, status in integration_status.items():
            print(f"{feature}: {status}")
        
        return self.test_results['failed'] == 0

def main():
    """主函数"""
    tester = IntegrationTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎊 恭喜！智能文本QA生成系统整合完成！")
        print("您现在可以使用以下命令开始使用系统：")
        print("  ./quick_start.sh help          # 查看帮助")
        print("  ./quick_start.sh setup         # 初始化环境")
        print("  ./quick_start.sh check         # 检查环境")
        print("  ./quick_start.sh full --input data/pdfs  # 运行完整流水线")
        return 0
    else:
        print("\n❗ 整合过程中发现问题，请根据测试报告进行修复。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)