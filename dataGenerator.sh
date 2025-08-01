# define two locations, input file location and output file location
# the location should be given as arguments to the scriptthe script with the input file and output file locations as arguments
if [ $# -eq 2 ]; then
    inputFileLocation=$1
    outputFileLocation=$2
    index1=$3
    index2=$4

    echo "Input File Location: $inputFileLocation"
    echo "Output File Location: $outputFileLocation"
    echo "Index 1: $index1"
    echo "Index 2: $index2"
else
    inputFileLocation="/mnt/data1/mllm/zc/tclreasoning/data/test_chinese/final_selected_folder"
    outputFileLocation="/mnt/data1/mllm/zc/tclreasoning/data/testoutput"
    index1=43
    index2=343
fi

# RUN python doubao_main.py
#python doubao_main.py --pdf_path $inputFileLocation --storage_folder $outputFileLocation --index $index1 --parallel_batch_size 25 --selected_task_number 500
#python clean_data.py --input_file "$outputFileLocation/total_responses.pkl" --output_file $outputFileLocation

#inputfile="$outputFileLocation/total_response.json"
#python qwen_argument.py --file_path $inputfile --image_folder $inputFileLocation --index $index2 
python qwen_argument.py --image_folder $inputFileLocation --index $index2 --check_task True