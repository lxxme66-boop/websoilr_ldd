from checkInfor.checkQuestion import *
if __name__ =="__main__":
    file_path = "/Users/Shared/VLReasoningTCL/data/bookoutput/book_checked/merged_data_qa_page30-41.csv"
    file_path2 = "/Users/Shared/VLReasoningTCL/data/bookoutput/book_checked/ppt_qa.xlsx"
    file_path3 = "/home/maxzhang/VLReasoningTCL/data/bookoutput/qwen_results_343.json"
    file_path4 = "/home/maxzhang/VLReasoningTCL/data/bookoutput/book_checked/merged_data_qa_page30-41_labeled.json"
    file_path5 = "/home/maxzhang/VLReasoningTCL/data/bookoutput/book_checked/image_qa.csv"
    file_path6 = "/Users/Shared/VLReasoningTCL/data/bookoutput/book_checked/ppt_qa.csv"
    file_path7 = "/mnt/data1/mllm/zc/tclreasoning/data/testoutput/qwen_results_343_filtered.csv"
    qa_labeler = QALabeler(activate_stream=True,parallel_core=10,
                           question_key="question",
                           answer_key="answer"
                           )
    qa_labeler.run_check(file_path7,use_img=False)
    
