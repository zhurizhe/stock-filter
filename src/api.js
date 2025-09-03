import axios from "axios";
import dotenv from "dotenv";
dotenv.config();

// 初始化 axios 实例
const api = axios.create({
    baseURL: process.env.EODPROXY_BASE_URL || "https://eodproxy.web-coding.tech/api/jit",
    timeout: 10000,
});

/**
 * 获取历史行情数据（支持多股票）
 * @param {string[]} symbols 股票代码数组，例如 ["600519.SHG", "000001.SHE"]
 * @param {string} start 开始日期 YYYY-MM-DD
 * @param {string} end 结束日期 YYYY-MM-DD
 * @returns {Promise<object>} 历史行情数据
 */
export async function getHistory(symbols, start, end) {
    try {
        const res = await api.post("/history", {
            symbols,
            start_date: start,
            end_date: end,
        });
        return res.data;
    } catch (err) {
        console.error("API getHistory Error:", err.message);
        return null;
    }
}

/**
 * 获取活跃股票列表
 * @param {string} exchange 交易所，如 "SHG" 或 "SHE"
 * @param {string} type 类型，如 "stock" 或 "etf"
 * @returns {Promise<object>} 股票列表
 */
export async function getActiveList(exchange, type = "stock") {
    try {
        const res = await api.post("/list-active", { exchange, type });
        return res.data;
    } catch (err) {
        console.error("API getActiveList Error:", err.message);
        return null;
    }
}

/**
 * 获取单只股票的最新行情（如需扩展可以调用 quote 接口）
 * @param {string} symbol 股票代码，例如 "600519.SHG"
 * @returns {Promise<object>} 最新行情数据
 */
export async function getQuote(symbol) {
    try {
        const res = await api.post("/quote", { symbols: [symbol] });
        return res.data;
    } catch (err) {
        console.error("API getQuote Error:", err.message);
        return null;
    }
}

/**
 * 获取财务数据（如果接口可用）
 * @param {string} symbol 股票代码
 * @returns {Promise<object>} 财务指标数据
 */
export async function getFundamentals(symbol) {
    try {
        const res = await api.post("/fundamentals", { symbols: [symbol] });
        return res.data;
    } catch (err) {
        console.error("API getFundamentals Error:", err.message);
        return null;
    }
}

export default {
    getHistory,
    getActiveList,
    getQuote,
    getFundamentals,
};