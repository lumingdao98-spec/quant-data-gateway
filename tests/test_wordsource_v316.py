from datetime import datetime, timedelta

from quant_data.models import Quote, Bar, AssetType
from quant_data.services.source_registry import SourceRegistryService
from quant_data.services.technical_factor_registry import TechnicalFactorRegistryService
from quant_data.services.candidate_pool_service import CandidatePoolService
from quant_data.services.wordsource_system_service import WordSourceSystemService
from quant_data.services.trading_framework_service import compute_indicator50_snapshot


def _bars(n=260):
    out=[]
    base=datetime(2025,1,1)
    price=10.0
    for i in range(n):
        price *= 1 + (0.001 if i%3 else -0.0005)
        out.append(Bar('600000','1d',base+timedelta(days=i),price*0.99,price*1.02,price*0.98,price,100000+i*100,price*100000,source='test'))
    return out


def _quote(sym='600000', name='浦发银行', amount=300_000_000, turnover=2.5, volume_ratio=1.6):
    return Quote(sym,name,datetime.now(),12,11.8,11.9,12.2,11.7,200000,amount,0.2,1.69,turnover=turnover,volume_ratio=volume_ratio,pe_dynamic=9,pb=0.8,float_market_cap=800_000_000_000,asset_type=AssetType.STOCK,source='test')


def test_source_registry_disables_search_engines():
    s=SourceRegistryService()
    disabled=s.disabled_sources()
    assert any('百度' in x['name'] for x in disabled)
    assert '宏观经济' in s.coverage_matrix()
    assert s.plan_for_target(180)['target_effective_items']==180


def test_technical_factor_registry_has_real_specs():
    r=TechnicalFactorRegistryService()
    cov=r.coverage()
    assert cov['total'] >= 50
    cats=r.by_category()
    assert '均线' in cats and '趋势/动量' in cats
    one=next(x for x in r.list() if x['key']=='rsi14')
    assert one['formula'] and one['bullish_rule'] and one['risk_rule']


def test_candidate_pool_three_channels():
    quotes=[_quote(f'600{i:03d}', f'测试{i}', amount=50_000_000+i*10_000_000, turnover=i%15, volume_ratio=1+(i%5)*0.5) for i in range(80)]
    pool=CandidatePoolService().build(quotes, max_items=60)
    assert pool['candidate_count'] > 0
    assert 'channel1' in pool['rules'] and 'channel2' in pool['rules'] and 'channel3' in pool['rules']
    assert any('technical_seed' in c['channels'] for c in pool['candidates'])


def test_wordsource_report_is_complete_and_not_empty():
    bars=_bars()
    q=_quote()
    opens=[b.open for b in bars]; highs=[b.high for b in bars]; lows=[b.low for b in bars]; closes=[b.close for b in bars]; vols=[b.volume for b in bars]; amts=[b.amount for b in bars]
    snap=compute_indicator50_snapshot(opens, highs, lows, closes, vols, amts)
    news=[{'title':'央行降准释放流动性，银行板块受关注','source':'央行','summary':'降准有利于流动性改善。','event_type':'policy'}]
    rep=WordSourceSystemService(feature_store_path='data/test_feature_store.sqlite').build_report(q,bars,snap,base_score=66,tags=['资金活跃'],risk_flags=[],news_items=news)
    assert rep['version'].startswith('3.16')
    assert rep['four_surface_scores']['technical'] > 0
    assert rep['information']['macro_policy']['has_macro_policy'] is True
    assert rep['strategy_signals']['signals']
    assert rep['position_risk']['risk_action']
