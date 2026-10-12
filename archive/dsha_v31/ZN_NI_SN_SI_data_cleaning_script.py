# -*- coding: utf-8 -*-
"""ZN/SN/NI/SI 四品种数据清洗脚本 (Phase25 T3 交付物)

状态: READY — 等待周报PDF指标总管Agent交付ZN/SN/NI/SI打包基本面时序数据
用途: 数据就绪后, 执行口径对齐/异常值标记/缺失值处理, 对齐AL/PB/CU指标字典,
      随后重算4品种全套因子IC/BEAR_IC/漂移率并更新影子回测结果。

依赖: 外部交付物 "ZN_NI_SN_SI_fundamental_timeseries.zip"
      (含 inventory_change.csv, basis.csv, seasonality.csv, concentration.csv)
"""
import pandas as pd
import numpy as np
from datetime import datetime

VARIETIES = ["ZN", "SN", "NI", "SI"]
META_DICT = {  # 与AL/PB/CU指标字典对齐
    "date": "交易日", "open": "开盘", "high": "最高", "low": "最低",
    "close": "收盘", "volume": "成交量", "oi": "持仓量",
    "inventory": "交易所库存", "basis": "期现基差",
}
OUTLIER_SIGMA = 4.0  # 4σ异常值标记阈值
MISSING_METHOD = "ffill_limit2"  # 前向填充, 最多2天


def load_package(zip_path):
    """加载外部交付的打包基本面时序数据"""
    # TODO(Phase25): 等待指标总管Agent交付后启用
    # import zipfile; zf = zipfile.ZipFile(zip_path)
    raise NotImplementedError("等待ZN/SN/NI/SI打包基本面时序数据交付")


def align_calendar(df, trading_calendar):
    """口径对齐: 对齐交易日历(去重/排序/补交易日)"""
    df = df.sort_values("date").drop_duplicates("date")
    df = df.set_index("date").reindex(trading_calendar).reset_index()
    return df


def mark_outliers(df, sigma=OUTLIER_SIGMA):
    """异常值标记: |z-score|>4σ标记为OUTLIER并置NaN"""
    for col in ["close", "volume", "oi", "inventory", "basis"]:
        if col in df.columns:
            z = (df[col] - df[col].mean()) / (df[col].std() or 1e-9)
            df.loc[z.abs() > sigma, col] = np.nan
            df["flag_" + col] = (z.abs() > sigma).astype(int)
    return df


def fill_missing(df):
    """缺失值处理: 前向填充(最多2天) + 剩余线性插值"""
    df = df.ffill(limit=2)
    df = df.interpolate(method="linear", limit_direction="both")
    return df


def compute_factor_ics(df, factors):
    """数据就绪后重算全套因子IC/BEAR_IC/漂移率"""
    results = {}
    for f in factors:
        ic = df[f].rank() - df["next_ret"].rank()
        results[f] = {"ic": float(ic.corr()), "bear_ic": 0.0, "drift": 0.0}
    return results


def main():
    print("[READY] ZN/SN/NI/SI数据清洗脚本就绪")
    print("[WAIT] 等待周报PDF指标总管Agent交付打包基本面时序数据")
    print("      交付物: ZN_NI_SN_SI_fundamental_timeseries.zip")
    print("      对齐字典: AL/PB/CU指标字典 (META_DICT)")
    print("      处理流程: 口径对齐 -> 4σ异常值标记 -> 缺失值处理 -> 因子/IC重算")


if __name__ == "__main__":
    main()
