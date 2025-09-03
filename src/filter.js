// 筛选逻辑函数集合

/**
 * 按价格区间筛选股票
 * @param {Array} stocks 历史数据数组（包含 symbol, rows）
 * @param {number} minPrice 最小股价
 * @param {number} maxPrice 最大股价
 * @returns {Array} 过滤后的股票
 */
export function filterByPrice(stocks, minPrice = 20, maxPrice = 40) {
  return stocks.filter(stock => {
    const last = stock.rows.at(-1);
    return last.close >= minPrice && last.close <= maxPrice;
  });
}

/**
 * 按成交额筛选股票
 * @param {Array} stocks 历史数据数组
 * @param {number} minAmount 最小成交额（单位：亿元）
 * @returns {Array} 过滤后的股票
 */
export function filterByAmount(stocks, minAmount = 20) {
  return stocks.filter(stock => {
    const last = stock.rows.at(-1);
    const amount = (last.close * last.volume) / 1e8; // 转换为亿元
    return amount >= minAmount;
  });
}

/**
 * 按换手率筛选股票（需自行计算流通市值）
 * @param {Array} stocks 历史数据数组
 * @param {number} minTurnoverRate 最小换手率（%）
 * @returns {Array} 过滤后的股票
 */
export function filterByTurnover(stocks, minTurnoverRate = 2) {
  // 注意：这里只是示例，实际换手率需要 = 成交量 / 流通股本
  return stocks.filter(stock => {
    const last = stock.rows.at(-1);
    // 这里暂用成交量与价格近似判断，未来可接入总股本计算
    const turnover = last.volume / 1e6; // 仅演示
    return turnover >= minTurnoverRate;
  });
}

/**
 * 组合筛选器：先按价格，再按成交额，再按换手率
 * @param {Array} stocks 历史数据数组
 * @returns {Array} 符合条件的股票
 */
export function combinedFilter(stocks) {
  let result = filterByPrice(stocks, 20, 40);
  result = filterByAmount(result, 20);
  result = filterByTurnover(result, 2);
  return result;
}

export default {
  filterByPrice,
  filterByAmount,
  filterByTurnover,
  combinedFilter,
};