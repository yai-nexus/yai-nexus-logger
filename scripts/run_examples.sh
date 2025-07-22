#!/bin/bash

# yai-nexus-logger 示例批量运行脚本
# 
# 这个脚本会自动发现并运行 examples/ 目录下的所有 Python 示例文件，
# 并收集它们的输出结果，用于验证日志功能是否正常工作。

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 全局变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EXAMPLES_DIR="$PROJECT_ROOT/examples"
TOTAL_EXAMPLES=0
SUCCESSFUL_EXAMPLES=0
FAILED_EXAMPLES=0
VERBOSE=false

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}❌ 未知参数: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -v, --verbose    显示详细输出"
    echo "  -h, --help       显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0               # 运行所有示例"
    echo "  $0 --verbose     # 运行所有示例并显示详细输出"
}

# 打印带颜色的标题
print_header() {
    echo -e "${BLUE}🚀 yai-nexus-logger 示例批量运行器${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

# 检查环境
check_environment() {
    echo -e "${CYAN}🔍 检查运行环境...${NC}"
    
    # 检查是否在正确的目录
    if [[ ! -d "$EXAMPLES_DIR" ]]; then
        echo -e "${RED}❌ 示例目录不存在: $EXAMPLES_DIR${NC}"
        echo -e "${YELLOW}💡 请确保在项目根目录运行此脚本${NC}"
        exit 1
    fi
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 未安装或不在 PATH 中${NC}"
        exit 1
    fi
    
    # 检查虚拟环境（推荐使用 .venv）
    if [[ -n "$VIRTUAL_ENV" ]]; then
        local venv_name=$(basename "$VIRTUAL_ENV")
        if [[ "$venv_name" == ".venv" ]]; then
            echo -e "${GREEN}✅ 检测到标准虚拟环境: .venv${NC}"
        else
            echo -e "${GREEN}✅ 检测到虚拟环境: $venv_name${NC}"
            echo -e "${YELLOW}💡 建议使用 .venv 作为虚拟环境目录名${NC}"
        fi
    elif [[ -d "$PROJECT_ROOT/.venv" ]]; then
        echo -e "${YELLOW}⚠️  发现 .venv 目录但未激活，请先激活虚拟环境:${NC}"
        echo -e "${YELLOW}   source .venv/bin/activate${NC}"
    else
        echo -e "${YELLOW}⚠️  未检测到虚拟环境，建议创建并使用 .venv:${NC}"
        echo -e "${YELLOW}   python3 -m venv .venv && source .venv/bin/activate${NC}"
    fi
    
    echo -e "${GREEN}✅ 环境检查完成${NC}"
    echo ""
}

# 发现示例文件
discover_examples() {
    echo -e "${CYAN}📋 发现示例文件...${NC}" >&2

    # 查找所有 .py 文件，排除 __init__.py 等
    local examples=()
    while IFS= read -r -d '' file; do
        local basename=$(basename "$file")
        if [[ ! "$basename" =~ ^__ ]]; then
            examples+=("$file")
        fi
    done < <(find "$EXAMPLES_DIR" -name "*.py" -type f -print0)

    TOTAL_EXAMPLES=${#examples[@]}

    if [[ $TOTAL_EXAMPLES -eq 0 ]]; then
        echo -e "${RED}❌ 没有发现任何示例文件${NC}" >&2
        exit 1
    fi

    echo -e "${GREEN}✅ 发现 $TOTAL_EXAMPLES 个示例文件${NC}" >&2
    for example in "${examples[@]}"; do
        echo -e "   📄 $(basename "$example")" >&2
    done
    echo "" >&2

    # 输出示例列表到标准输出
    printf '%s\n' "${examples[@]}"
}

# 运行单个示例
run_example() {
    local example_path="$1"
    local example_name=$(basename "$example_path")
    local start_time=$(date +%s)

    echo -e "${PURPLE}🚀 运行示例: $example_name${NC}"

    # 创建临时文件存储输出
    local stdout_file=$(mktemp)
    local stderr_file=$(mktemp)
    local exit_code=0

    # 运行示例，设置超时为30秒
    # 使用 gtimeout (macOS) 或 timeout (Linux)
    local timeout_cmd=""
    if command -v gtimeout &> /dev/null; then
        timeout_cmd="gtimeout 30s"
    elif command -v timeout &> /dev/null; then
        timeout_cmd="timeout 30s"
    else
        timeout_cmd=""
    fi

    # 为 FastAPI 示例设置测试模式
    local env_vars=""
    if [[ "$example_name" == *"fastapi"* ]] || [[ "$example_name" == *"trace_id"* ]]; then
        env_vars="TEST_MODE=1"
    fi

    if [[ -n "$timeout_cmd" ]]; then
        if env $env_vars $timeout_cmd python3 "$example_path" > "$stdout_file" 2> "$stderr_file"; then
            exit_code=0
        else
            exit_code=$?
        fi
    else
        # 没有 timeout 命令，直接运行
        if env $env_vars python3 "$example_path" > "$stdout_file" 2> "$stderr_file"; then
            exit_code=0
        else
            exit_code=$?
        fi
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # 读取输出
    local stdout_content=$(cat "$stdout_file")
    local stderr_content=$(cat "$stderr_file")
    
    # 分析输出
    analyze_output "$stdout_content" "$stderr_content" "$example_name" "$duration" "$exit_code"
    
    # 清理临时文件
    rm -f "$stdout_file" "$stderr_file"
    
    return $exit_code
}

# 分析输出
analyze_output() {
    local stdout="$1"
    local stderr="$2"
    local example_name="$3"
    local duration="$4"
    local exit_code="$5"
    
    local all_output="$stdout$stderr"
    local line_count=$(echo "$all_output" | grep -c '^' || echo "0")
    local has_logs=false
    local log_levels=()
    local has_trace_id=false
    local has_structured_data=false
    
    # 检查日志级别
    if echo "$all_output" | grep -q "DEBUG"; then log_levels+=("DEBUG"); has_logs=true; fi
    if echo "$all_output" | grep -q "INFO"; then log_levels+=("INFO"); has_logs=true; fi
    if echo "$all_output" | grep -q "WARNING"; then log_levels+=("WARNING"); has_logs=true; fi
    if echo "$all_output" | grep -q "ERROR"; then log_levels+=("ERROR"); has_logs=true; fi
    if echo "$all_output" | grep -q "CRITICAL"; then log_levels+=("CRITICAL"); has_logs=true; fi
    
    # 检查 trace_id
    if echo "$all_output" | grep -qi "trace.id\|trace-id"; then
        has_trace_id=true
    fi
    
    # 检查结构化数据
    if echo "$all_output" | grep -q "{.*}"; then
        has_structured_data=true
    fi
    
    # 显示结果
    if [[ $exit_code -eq 0 ]]; then
        echo -e "   ${GREEN}✅ 成功 - ${duration%.*}s${NC}"
        ((SUCCESSFUL_EXAMPLES++))
        
        echo -e "   📊 输出行数: $line_count"
        if [[ ${#log_levels[@]} -gt 0 ]]; then
            echo -e "   📝 日志级别: $(IFS=', '; echo "${log_levels[*]}")"
        fi
        if [[ "$has_trace_id" == true ]]; then
            echo -e "   🔍 包含 trace_id"
        fi
        if [[ "$has_structured_data" == true ]]; then
            echo -e "   📋 包含结构化数据"
        fi
        
        # 详细输出模式
        if [[ "$VERBOSE" == true ]]; then
            echo -e "   ${CYAN}--- 标准输出 ---${NC}"
            echo "$stdout" | sed 's/^/   /'
            if [[ -n "$stderr" ]]; then
                echo -e "   ${YELLOW}--- 标准错误 ---${NC}"
                echo "$stderr" | sed 's/^/   /'
            fi
        fi
    else
        echo -e "   ${RED}❌ 失败 - ${duration%.*}s${NC}"
        ((FAILED_EXAMPLES++))
        
        if [[ -n "$stderr" ]]; then
            echo -e "   ${RED}错误信息:${NC}"
            echo "$stderr" | head -3 | sed 's/^/   /'
        fi
        
        if [[ "$VERBOSE" == true && -n "$stdout" ]]; then
            echo -e "   ${CYAN}--- 标准输出 ---${NC}"
            echo "$stdout" | sed 's/^/   /'
        fi
    fi
    
    echo -e "${CYAN}----------------------------------------${NC}"
}

# 打印总结
print_summary() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}📊 运行总结${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo -e "总计: $TOTAL_EXAMPLES 个示例"
    echo -e "${GREEN}成功: $SUCCESSFUL_EXAMPLES 个 ✅${NC}"
    echo -e "${RED}失败: $FAILED_EXAMPLES 个 ❌${NC}"
    
    if [[ $FAILED_EXAMPLES -gt 0 ]]; then
        echo ""
        echo -e "${RED}❌ 有示例运行失败，请检查上面的错误信息${NC}"
        echo -e "${YELLOW}💡 建议使用 --verbose 参数查看详细输出${NC}"
    else
        echo ""
        echo -e "${GREEN}🎉 所有示例都运行成功！${NC}"
        echo -e "${GREEN}✅ yai-nexus-logger 日志功能正常工作${NC}"
    fi
}

# 主函数
main() {
    parse_args "$@"
    print_header
    check_environment
    
    # 发现并运行示例
    local examples=()
    while IFS= read -r line; do
        examples+=("$line")
    done < <(discover_examples)
    
    echo -e "${BLUE}============================================================${NC}"
    
    for example in "${examples[@]}"; do
        run_example "$example"
    done
    
    print_summary
    
    # 根据结果设置退出码
    if [[ $FAILED_EXAMPLES -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# 运行主函数
main "$@"
