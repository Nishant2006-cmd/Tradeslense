import argparse
import json
import os
from datetime import datetime, timedelta
import pandas as pd

def parse_args():
    parser = argparse.ArgumentParser(description="TradeLens Engine")
    parser.add_argument("--data", required=True, help="Path to data directory")
    parser.add_argument("--rules", required=True, help="Path to rules.json")
    parser.add_argument("--out", required=True, help="Path to output directory")
    return parser.parse_args()

def get_asset_class(symbol):
    s = symbol.upper()
    if s.startswith(("XAU", "XAG")):
        return "metals"
    elif s.startswith(("EUR", "GBP", "USD")):
        return "forex"
    elif s.startswith(("BTC", "ETH")):
        return "crypto"
    elif s.startswith(("NIFTY", "BANKNIFTY", "FINNIFTY")):
        return "index_options"
    else:
        return "other"

def clean_symbol(raw_symbol):
    if not isinstance(raw_symbol, str):
        return ""
    return raw_symbol.split(".")[0].upper()
def process_mt5_csv(filepath):
    df = None
    for sep in ["\t", ",", ";"]:
        for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
            try:
                temp_df = pd.read_csv(filepath, encoding=enc, sep=sep, on_bad_lines="skip")
                if temp_df.shape[1] > 1:
                    df = temp_df
                    break
            except Exception:
                continue
        if df is not None:
            break
            
    if df is None:
        df = pd.read_csv(filepath, encoding="latin-1", on_bad_lines="skip")
        
    trades = []
    
    for _, row in df.iterrows():
        t_type = str(row.get("Type", "")).lower()
        if t_type not in ["buy", "sell"]:
            continue
            
        ticket = row.get("Ticket")
        if pd.isna(ticket):
            continue
            
        trade_id = f"mt5-{int(ticket)}"
        raw_symbol = str(row.get("Symbol", ""))
        symbol = clean_symbol(raw_symbol)
        asset_class = get_asset_class(symbol)
        
        time_str = str(row.get("Time", ""))
        try:
            dt_utc = datetime.strptime(time_str.replace(".", "-"), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                dt_utc = pd.to_datetime(time_str, errors='coerce')
                if pd.isna(dt_utc):
                    continue
                dt_utc = dt_utc.to_pydatetime()
            except Exception:
                continue
                
        if pd.isna(dt_utc):
            continue
                
        dt_ist = dt_utc + timedelta(hours=5, minutes=30)
        close_date = dt_ist.strftime("%Y-%m-%d")
        close_time = dt_ist.strftime("%H:%M:%S")
        
        quantity = float(row.get("Volume", 0.0))
        profit = float(row.get("Profit", 0.0))
        commission = float(row.get("Commission", 0.0))
        swap = float(row.get("Swap", 0.0))
        
        pnl_native = round(profit + commission + swap, 2)
        
        trades.append({
            "trade_id": trade_id,
            "source": "mt5",
            "symbol": symbol,
            "asset_class": asset_class,
            "close_date": close_date,
            "close_time": close_time,
            "quantity": quantity,
            "pnl_native": pnl_native,
            "currency": "USD",
            "_dt_ist": dt_ist
        })
    return trades

def process_broker_excel(filepath):
    raw_df = pd.read_excel(filepath, header=None)
    header_row_idx = None
    
    for idx, row in raw_df.iterrows():
        row_str = " ".join([str(val) for val in row.values])
        if "Order ID" in row_str or "Trade Date" in row_str or "Realized P&L" in row_str or "Symbol" in row_str:
            header_row_idx = idx
            break
            
    if header_row_idx is not None:
        df = pd.read_excel(filepath, header=header_row_idx)
    else:
        df = pd.read_excel(filepath)
        
    trades = []
    for _, row in df.iterrows():
        order_id = None
        for col in df.columns:
            if "order" in str(col).lower() and "id" in str(col).lower():
                order_id = row[col]
                break
        if order_id is None or pd.isna(order_id):
            for col in ["Order ID", "OrderNo", "Order ID/Trade ID"]:
                if col in df.columns:
                    order_id = row[col]
                    break
        if order_id is None or pd.isna(order_id):
            continue
            
        if "total" in str(order_id).lower():
            continue
            
        trade_id = f"in-{int(order_id) if isinstance(order_id, (int, float)) else order_id}"
        
        raw_symbol = ""
        for col in df.columns:
            if "symbol" in str(col).lower():
                raw_symbol = str(row[col])
                break
        symbol = clean_symbol(raw_symbol)
        asset_class = get_asset_class(symbol)
        
        date_val = None
        for col in df.columns:
            if "date" in str(col).lower():
                date_val = row[col]
                break
        
        if pd.isna(date_val):
            continue
            
        if isinstance(date_val, datetime):
            close_date = date_val.strftime("%Y-%m-%d")
        else:
            date_str = str(date_val).strip()
            parsed_dt = pd.to_datetime(date_str, errors='coerce', dayfirst=True)
            if pd.isna(parsed_dt):
                continue
            close_date = parsed_dt.strftime("%Y-%m-%d")
            
        qty = 0.0
        for col in df.columns:
            if "qty" in str(col).lower() or "quantity" in str(col).lower():
                try:
                    qty = float(row[col])
                except Exception:
                    pass
                break
                
        pnl_val = 0.0
        for col in df.columns:
            if "p&l" in str(col).lower() or "realized" in str(col).lower() or "profit" in str(col).lower():
                val_str = str(row[col]).replace(",", "").strip()
                try:
                    pnl_val = float(val_str)
                except Exception:
                    pass
                break
                
        pnl_native = round(pnl_val, 2)
        
        trades.append({
            "trade_id": trade_id,
            "source": "broker_in",
            "symbol": symbol,
            "asset_class": asset_class,
            "close_date": close_date,
            "close_time": "",
            "quantity": qty,
            "pnl_native": pnl_native,
            "currency": "INR",
            "_dt_ist": datetime.strptime(close_date, "%Y-%m-%d")
        })
    return trades

def main():
    args = parse_args()
    os.makedirs(args.out, exist_ok=True)
    
    with open(args.rules, "r") as f:
        rules = json.load(f)
    usd_inr = float(rules.get("usd_inr", 84.0))
    
    all_trades = []
    
    for root, _, files in os.walk(args.data):
        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith(".csv"):
                all_trades.extend(process_mt5_csv(filepath))
            elif file.endswith(".xlsx") or file.endswith(".xls"):
                all_trades.extend(process_broker_excel(filepath))
                
    unique_trades_dict = {}
    for t in all_trades:
        tid = t["trade_id"]
        unique_trades_dict[tid] = t
        
    trades_list = list(unique_trades_dict.values())
    
    for t in trades_list:
        if t["currency"] == "USD":
            t["pnl_inr"] = round(t["pnl_native"] * usd_inr, 2)
        else:
            t["pnl_inr"] = round(t["pnl_native"], 2)
            
    trades_list.sort(key=lambda x: (x["close_date"], x["close_time"] if x["close_time"] else "00:00:00", x["trade_id"]))
    
    trades_csv_path = os.path.join(args.out, "trades.csv")
    trade_columns = ["trade_id", "source", "symbol", "asset_class", "close_date", "close_time", "quantity", "pnl_native", "currency", "pnl_inr"]
    
    df_out = pd.DataFrame(trades_list)
    for col in trade_columns:
        if col not in df_out.columns:
            df_out[col] = ""
    df_out = df_out[trade_columns]
    df_out.to_csv(trades_csv_path, index=False)
    
    total_trades = len(trades_list)
    winning_trades = sum(1 for t in trades_list if t["pnl_inr"] > 0)
    losing_trades = sum(1 for t in trades_list if t["pnl_inr"] < 0)
    win_rate = round(winning_trades / total_trades, 4) if total_trades > 0 else 0.0
    net_pnl_inr = round(sum(t["pnl_inr"] for t in trades_list), 2)
    
    by_asset_class = {}
    ac_groups = {}
    for t in trades_list:
        ac = t["asset_class"]
        if ac not in ac_groups:
            ac_groups[ac] = {"trades": 0, "net_pnl_inr": 0.0}
        ac_groups[ac]["trades"] += 1
        ac_groups[ac]["net_pnl_inr"] = round(ac_groups[ac]["net_pnl_inr"] + t["pnl_inr"], 2)
        
    for ac, vals in sorted(ac_groups.items()):
        by_asset_class[ac] = vals
        
    daily_groups = {}
    for t in trades_list:
        d = t["close_date"]
        if d not in daily_groups:
            daily_groups[d] = {"trades": 0, "net_pnl_inr": 0.0}
        daily_groups[d]["trades"] += 1
        daily_groups[d]["net_pnl_inr"] = round(daily_groups[d]["net_pnl_inr"] + t["pnl_inr"], 2)
        
    daily_list = []
    cumulative_pnl = 0.0
    for d in sorted(daily_groups.keys()):
        pnl = daily_groups[d]["net_pnl_inr"]
        cumulative_pnl = round(cumulative_pnl + pnl, 2)
        daily_list.append({
            "date": d,
            "trades": daily_groups[d]["trades"],
            "net_pnl_inr": pnl,
            "cumulative_pnl_inr": cumulative_pnl
        })
        
    summary_data = {
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": win_rate,
        "net_pnl_inr": net_pnl_inr,
        "by_asset_class": by_asset_class,
        "daily": daily_list
    }
    
    with open(os.path.join(args.out, "summary.json"), "w") as f:
        json.dump(summary_data, f, indent=2)
        
    violations = []
    rule_limits = rules.get("limits", {})
    
    max_trades_limit = rule_limits.get("max_trades_per_day")
    max_loss_limit = rule_limits.get("max_daily_loss_inr")
    max_consec_losses_limit = rule_limits.get("stop_after_consecutive_losses")
    max_lot_limit = rule_limits.get("max_lot_size")
    
    trades_by_date = {}
    for t in trades_list:
        d = t["close_date"]
        if d not in trades_by_date:
            trades_by_date[d] = []
        trades_by_date[d].append(t)
        
    for d, d_trades in trades_by_date.items():
        if max_trades_limit is not None and len(d_trades) > max_trades_limit:
            violations.append({
                "date": d,
                "rule_id": "max_trades_per_day",
                "detail": f"{len(d_trades)} trades (limit {max_trades_limit})"
            })
            
        day_pnl = sum(t["pnl_inr"] for t in d_trades)
        if max_loss_limit is not None and day_pnl < -abs(max_loss_limit):
            violations.append({
                "date": d,
                "rule_id": "max_daily_loss_inr",
                "detail": f"Day PnL INR {day_pnl} below limit -{max_loss_limit}"
            })
            
        if max_lot_limit is not None:
            for t in d_trades:
                if t["source"] == "mt5" and t["quantity"] > max_lot_limit:
                    violations.append({
                        "date": d,
                        "rule_id": "max_lot_size",
                        "detail": f"Lot size {t['quantity']} exceeds limit {max_lot_limit} for trade {t['trade_id']}"
                    })
                    
        if max_consec_losses_limit is not None:
            mt5_d_trades = [t for t in d_trades if t["source"] == "mt5" and t["close_time"] != ""]
            mt5_d_trades.sort(key=lambda x: x["close_time"])
            
            consec_losses = 0
            broken_recorded = False
            for t in mt5_d_trades:
                if consec_losses >= max_consec_losses_limit and not broken_recorded:
                    violations.append({
                        "date": d,
                        "rule_id": "stop_after_consecutive_losses",
                        "detail": f"Trade {t['trade_id']} executed after {consec_losses} consecutive losses (limit {max_consec_losses_limit})"
                    })
                    broken_recorded = True
                
                if t["pnl_native"] < 0:
                    consec_losses += 1
                else:
                    consec_losses = 0
                    
    df_viol = pd.DataFrame(violations)
    if df_viol.empty:
        df_viol = pd.DataFrame(columns=["date", "rule_id", "detail"])
    df_viol.to_csv(os.path.join(args.out, "violations.csv"), index=False)
    
    report_content = f"""# Weekly Trading Discipline Report

- **Total Trades:** {total_trades}
- **Win Rate:** {{:.1f}}% ({winning_trades} wins / {losing_trades} losses)
- **Net PnL:** ₹{net_pnl_inr:,.2f}
- **Rule Violations Detected:** {len(violations)}

## Performance Review
During this trading period, you took a total of {total_trades} trades resulting in a net PnL of ₹{net_pnl_inr:,.2f}. Your win rate stands at {win_rate * 100:.1f}%. 

## Discipline & Risk Management
{'No major rule violations were recorded.' if len(violations) == 0 else f'A total of {len(violations)} rule infraction(s) were flagged in `violations.csv`. Review your daily risk limits and consecutive loss thresholds.'} 

Maintain strict adherence to your risk management parameters to ensure long-term consistency.
""".format(win_rate * 100)

    with open(os.path.join(args.out, "report.md"), "w",encoding="utf-8") as f:
        f.write(report_content)

if __name__ == "__main__":
    main()