"""Reproduce MIA 5130 Milestone 3 from the uploaded Milestone 2 panel.

Run: python Milestone3_Reproduce.py --data-dir /path/to/dataset --output-dir ./milestone3_support
Requires NumPy; the figures can be viewed in the accompanying report. This script uses the exact ridge design and
ridge alpha=100 chosen during Milestone 2; it does NOT use future outcomes.
The Milestone 3 method is an analytical, integer-unit allocation, not an external solver.
"""
from __future__ import annotations
import argparse, csv, json, math
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
import numpy as np

FEATURES = [
    'sales_lag_1w','sales_lag_2w','sales_lag_4w','sales_lag_52w',
    'sales_mean_4w','sales_mean_8w','sales_std_4w','last_observed_price',
    'price_age_days','snap_days','event_days','target_month','target_year','target_weekofyear'
]
ITEM_ORDER = ['FOODS_3_586','FOODS_3_252','FOODS_3_714','FOODS_3_607','FOODS_3_064',
              'FOODS_3_555','FOODS_2_197','FOODS_3_739','FOODS_3_501','FOODS_3_099']
CAPACITY = 100
PROPORTION_TOLERANCE = 0.20
ORIGIN = date(2016, 5, 22)
FUTURE_WEEK_START, FUTURE_WEEK_END = ORIGIN+timedelta(days=1), ORIGIN+timedelta(days=7)

def load_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fields=None):
    if not rows: raise ValueError('Cannot export empty table')
    fields = list(rows[0]) if fields is None else fields
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader();w.writerows(rows)

def ridge_fit(panel):
    tr=[r for r in panel if r['split']=='train']
    assert len(tr)==1553
    levels=sorted(set(r['item_id'] for r in tr))
    numeric=np.array([[float(r[f]) for f in FEATURES] for r in tr],dtype=float)
    means=numeric.mean(axis=0); scales=numeric.std(axis=0,ddof=0);scales=np.where(scales>0,scales,1.0)
    def design(rows):
        raw=np.array([[float(r[f]) for f in FEATURES] for r in rows],dtype=float)
        dummies=[np.array([1.0 if r['item_id']==i else 0.0 for r in rows]) for i in levels[1:]]
        return np.column_stack([np.ones(len(rows)),(raw-means)/scales]+dummies)
    X=design(tr); y=np.array([float(r['target_units']) for r in tr]); alpha=100.0
    penalty=np.eye(X.shape[1]);penalty[0,0]=0
    beta,*_=np.linalg.lstsq(np.vstack([X,np.sqrt(alpha)*penalty]),np.r_[y,np.zeros(X.shape[1])],rcond=None)
    def predict(rows): return np.maximum(design(rows)@beta,0)
    test=[r for r in panel if r['split']=='test']
    test_y=np.array([float(r['target_units']) for r in test]);pr=predict(test)
    mae=float(np.mean(np.abs(test_y-pr))); rmse=float(np.sqrt(np.mean((test_y-pr)**2)))
    assert len(test)==560 and abs(mae-25.117915977858836)<1e-6 and abs(rmse-36.512154705449625)<1e-6, (mae,rmse)
    return predict, {'test_observations':len(test),'test_MAE':mae,'test_RMSE':rmse,
                     'train_rows':len(tr),'train_cutoff':'2015-03-01','ridge_alpha':alpha}

def price_asof(data_dir, calendar, items):
    completed_week_fridays={}
    for r in calendar:
        d=date.fromisoformat(r['date'])
        if d.weekday()==4 and d<=ORIGIN:
            completed_week_fridays[r['wm_yr_wk']]=d
    chosen={}
    price_file=(data_dir/'sell_prices.csv') if (data_dir/'sell_prices.csv').exists() else (data_dir/'m3_selected_price_history.csv')
    with open(price_file,newline='',encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if row['store_id']!='CA_1' or row['item_id'] not in items: continue
            d=completed_week_fridays.get(row['wm_yr_wk'])
            if d is not None and (row['item_id'] not in chosen or chosen[row['item_id']]['price_information_date']<d):
                chosen[row['item_id']]={'price_information_date':d,'sell_price':float(row['sell_price']),
                                        'price_record_week':row['wm_yr_wk']}
    assert set(chosen)==set(items)
    assert all(p['price_information_date']<=ORIGIN for p in chosen.values())
    return chosen

def next_week_rows(panel, calendar, prices):
    cal_by_date={r['date']:r for r in calendar}
    future=[cal_by_date[(FUTURE_WEEK_START+timedelta(days=i)).isoformat()] for i in range(7)]
    snap=sum(int(r['snap_CA']) for r in future)
    event=sum(bool(r['event_name_1']) or bool(r['event_name_2']) for r in future)
    history=defaultdict(list)
    for r in panel: history[r['item_id']].append(r)
    out=[]
    for item in ITEM_ORDER:
        past=sorted(history[item],key=lambda r:r['week_start'])
        assert past[-1]['week_end']==ORIGIN.isoformat() and len(past)>52
        values=np.array([float(r['target_units']) for r in past]); price=prices[item]
        row={**past[-1]}
        row.update({'forecast_origin':ORIGIN.isoformat(),'week_start':FUTURE_WEEK_START.isoformat(),
                    'week_end':FUTURE_WEEK_END.isoformat(),'sales_information_date':ORIGIN.isoformat(),
                    'last_observed_price':str(price['sell_price']),
                    'price_information_date':price['price_information_date'].isoformat(),
                    'price_record_week':price['price_record_week'],
                    'price_age_days':str((ORIGIN-price['price_information_date']).days),
                    'snap_days':str(snap),'event_days':str(event),
                    'target_month':str(FUTURE_WEEK_START.month),'target_year':str(FUTURE_WEEK_START.year),
                    'target_weekofyear':str(FUTURE_WEEK_START.isocalendar().week),
                    'history_weeks_available':str(int(past[-1]['history_weeks_available'])+1),
                    'split':'future','target_quarter':'2016Q2'})
        for lag in [1,2,4,52]:row[f'sales_lag_{lag}w']=str(values[-lag])
        for n in [4,8]:row[f'sales_mean_{n}w']=str(values[-n:].mean())
        row['sales_std_4w']=str(values[-4:].std(ddof=1))
        row.pop('target_units',None)
        out.append(row)
    return out

def hamilton(forecast):
    demand=np.array(forecast,dtype=float)
    assert np.all(demand>0) and demand.sum()>=CAPACITY
    quotas=CAPACITY*demand/demand.sum()
    units=np.floor(quotas).astype(int)
    to_award=CAPACITY-int(units.sum())
    ranked=sorted(range(len(units)),key=lambda i:(-(quotas[i]-math.floor(quotas[i])),ITEM_ORDER[i]))
    for i in ranked[:to_award]:units[i]+=1
    assert int(units.sum())==CAPACITY and np.all(units<=demand)
    return quotas,units,ranked[:to_award]

def bounded_revenue_maximizer(quotas,forecasts,prices):
    """Exchange-optimal integer solution with bounded proportionality.

    Starting from product minimums, assign each residual unit to the highest
    priced product with available capacity. Equal unit weights and linear
    marginal revenues make this greedy allocation globally optimal.
    """
    lo=np.floor((1.0-PROPORTION_TOLERANCE)*quotas).astype(int)
    hi=np.ceil((1.0+PROPORTION_TOLERANCE)*quotas).astype(int)
    hi=np.minimum(hi,np.floor(forecasts).astype(int))
    assert np.all(lo<=hi) and sum(lo)<=CAPACITY<=sum(hi)
    units=lo.copy();remain=CAPACITY-int(sum(units));steps=[]
    for i in sorted(range(len(units)),key=lambda i:(-prices[i],ITEM_ORDER[i])):
        if remain==0:break
        add=min(int(hi[i]-units[i]),remain)
        if add:
            units[i]+=add;remain-=add
            steps.append({'sequence':len(steps)+1,'product_id':ITEM_ORDER[i],
                          'price_usd':f'{prices[i]:.2f}','minimum_units':int(lo[i]),
                          'added_units':add,'final_units_for_product':int(units[i]),
                          'remaining_capacity_after_step':remain,
                          'incremental_revenue_usd':f'{prices[i]*add:.2f}'})
    assert remain==0 and sum(units)==CAPACITY and np.all(units>=lo) and np.all(units<=hi)
    return lo,hi,units,steps

def main(data_dir,output_dir):
    output_dir.mkdir(parents=True,exist_ok=True)
    panel=load_csv(data_dir/'weekly_forecasting_panel.csv'); calendar=load_csv(data_dir/'calendar.csv')
    assert set(r['item_id'] for r in panel)==set(ITEM_ORDER)
    assert set(r['store_id'] for r in panel)=={'CA_1'}
    predict,verification=ridge_fit(panel)
    price_lookup=price_asof(data_dir,calendar,set(ITEM_ORDER))
    rows=next_week_rows(panel,calendar,price_lookup)
    predictions=predict(rows);prices=np.array([price_lookup[i]['sell_price'] for i in ITEM_ORDER])
    quotas,x1,remainder_awards=hamilton(predictions)
    lower,upper,x2,steps=bounded_revenue_maximizer(quotas,predictions,prices)
    # Independently verify greedy optimum by checking every more expensive product is filled
    # before a lower priced product is awarded any above-minimum unit.
    for i in range(len(ITEM_ORDER)):
        for j in range(len(ITEM_ORDER)):
            if prices[i]>prices[j] and x2[i]<upper[i] and x2[j]>lower[j]:
                raise AssertionError('Profitable unit-exchange available; not optimal')
    forecast_rows=[]; s1=[]; s2=[]
    for k,item in enumerate(ITEM_ORDER):
        fr={'Product_ID':item,'Store_ID':'CA_1','Forecast_Origin':ORIGIN.isoformat(),
            'Week_Start':FUTURE_WEEK_START.isoformat(),'Week_End':FUTURE_WEEK_END.isoformat(),
            'Forecast_Model':'Milestone 2 validation-selected lag-based ridge; alpha=100; frozen 2015-03-01 coefficients',
            'Forecasted_Demand':round(float(predictions[k]),6),
            'sell_price_USD':f'{prices[k]:.2f}',
            'Price_Information_Date':price_lookup[item]['price_information_date'].isoformat(),
            'Price_Record_Week':price_lookup[item]['price_record_week'],
            'Sales_Lag_1w':int(float(rows[k]['sales_lag_1w'])),
            'Sales_Mean_4w':round(float(rows[k]['sales_mean_4w']),4),
            'No_Actual_Future_Sales_Used':True}
        forecast_rows.append(fr)
        s1.append({'Product_ID':item,'Forecasted_Demand':round(float(predictions[k]),6),
                   'sell_price_USD':f'{prices[k]:.2f}',
                   'Demand_Share_Pct':round(float(100*predictions[k]/sum(predictions)),4),
                   'Exact_100_Unit_Quota':round(float(quotas[k]),6),
                   'Floor_Quota':int(math.floor(quotas[k])),
                   'Largest_Remainder_Awarded':int(k in remainder_awards),
                   'Allocated_Inventory':int(x1[k]),
                   'Revenue_USD':f'{int(x1[k])*prices[k]:.2f}'})
        s2.append({'Product_ID':item,'Forecasted_Demand':round(float(predictions[k]),6),
                   'sell_price_USD':f'{prices[k]:.2f}',
                   'Exact_100_Unit_Quota':round(float(quotas[k]),6),
                   'Min_Units_80pct_Quota_Floor':int(lower[k]),
                   'Max_Units_120pct_Quota_Ceil':int(upper[k]),
                   'Allocated_Inventory':int(x2[k]),
                   'Difference_From_Scenario1':int(x2[k]-x1[k]),
                   'Revenue_USD':f'{int(x2[k])*prices[k]:.2f}'})
    rev1=float(np.dot(prices,x1));rev2=float(np.dot(prices,x2))
    write_csv(output_dir/'m3_forecast_handoff.csv',forecast_rows)
    write_csv(output_dir/'m3_scenario1_proportional.csv',s1)
    write_csv(output_dir/'m3_scenario2_bounded_revenue_optimal.csv',s2)
    write_csv(output_dir/'m3_analytical_solution_steps.csv',steps)
    orig1=load_csv(data_dir/'scenario1_proportional_allocation (2).csv')
    orig2=load_csv(data_dir/'scenario2_revenue_maximization (2).csv')
    orig1={r['Product_ID']:r for r in orig1};orig2={r['Product_ID']:r for r in orig2}
    audit=[{'Product_ID':item,'Original_Forecasted_Demand':orig1[item]['Forecasted_Demand'],
            'Reproduced_Ridge_Forecasted_Demand':f'{predictions[i]:.6f}',
            'Original_Sell_Price_USD':orig1[item]['sell_price'],
            'AsOf_2016_05_20_Sell_Price_USD':f'{prices[i]:.2f}',
            'Original_Scenario1_Units':orig1[item]['Allocated_Inventory'],
            'Original_Scenario2_Units':orig2[item]['Allocated_Inventory'],
            'Reproduced_Scenario1_Units':int(x1[i]),
            'Reproduced_Scenario2_Units':int(x2[i]),
            'Original_Inputs_Undated':True} for i,item in enumerate(ITEM_ORDER)]
    write_csv(output_dir/'m3_original_vs_reproduced_audit.csv',audit)
    summary={'method':'Analytical largest-remainder apportionment + price-ordered bounded integer allocation',
        'pricing_currency':'USD','store_id':'CA_1','forecast_origin':ORIGIN.isoformat(),
        'forecast_start':FUTURE_WEEK_START.isoformat(),'forecast_end':FUTURE_WEEK_END.isoformat(),
        'forecasting_model':'Milestone 2 lag-based ridge regression, alpha=100; fit ends 2015-03-01',
        'm2_reproduced_check':verification,'forecast_total_units':float(sum(predictions)),
        'capacity_units':CAPACITY,'proportionality_tolerance_fraction':PROPORTION_TOLERANCE,
        'scenario1_allocated_units':int(sum(x1)),'scenario1_revenue_usd':round(rev1,2),
        'scenario2_allocated_units':int(sum(x2)),'scenario2_revenue_usd':round(rev2,2),
        'revenue_increase_usd':round(rev2-rev1,2),
        'revenue_increase_pct':float(100*(rev2/rev1-1)),
        'scenario1_total_abs_quota_deviation':float(sum(abs(x1-quotas))),
        'scenario2_total_abs_quota_deviation':float(sum(abs(x2-quotas))),
        'all_units_below_forecast':bool(np.all(x1<=predictions) and np.all(x2<=predictions)),
        'price_information_dates':sorted(set(p['price_information_date'].isoformat() for p in price_lookup.values())),
        'original_supplied_scenario1_revenue_usd':206.40,
        'original_supplied_scenario2_revenue_usd':254.74,
        'notes':['These are conditional potential sales revenues (not profits).',
                 'Original allocation inputs were undated and did not reconcile to the reproduced ridge forecasts and latest known completed-week prices.',
                 '20% proportionality band is an explicit policy assumption, not part of the M5 dataset or coursework brief.',
                 'Selling prices use last fully completed retail week ending May 20, 2016, and may differ during forecast week.',
                 'Future demand is unobserved in the source data. No future labels are used.']}
    (output_dir/'m3_summary_reproduced.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    return summary,forecast_rows,s1,s2,steps

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-dir',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent/'Milestone3_Support')
    args=p.parse_args();main(args.data_dir,args.output_dir)
