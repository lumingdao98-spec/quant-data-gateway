from __future__ import annotations
import re

class ResearchReportService:
    def parse(self, text:str)->dict:
        text=text or ""
        rating=None; direction="neutral"; signals=[]
        for kw in ["买入","强烈推荐","增持","推荐","上调目标价","首次覆盖"]:
            if kw in text: rating=kw; direction="positive"; signals.append(kw)
        for kw in ["下调评级","低于预期","不及预期","下修盈利","减持","卖出"]:
            if kw in text: rating=kw; direction="negative"; signals.append(kw)
        target_price=None
        m=re.search(r"目标价[为至]?\s*([0-9]+(?:\.[0-9]+)?)",text)
        if m: target_price=float(m.group(1))
        return {"is_research_like": any(k in text for k in ["研报","评级","目标价","EPS","盈利预测","分析师"]), "rating_signal":rating,"direction":direction,"target_price":target_price,"signals":signals}

class SentimentObserverService:
    POS=["看好","利好","买入","加仓","涨停","反弹","超预期","龙头","强势"]
    NEG=["看空","利空","减仓","暴跌","亏损","不及预期","爆雷","退潮","套牢","下跌"]
    def analyze_texts(self, texts:list[str])->dict:
        pos=neg=neu=0
        for t in texts or []:
            p=sum(1 for k in self.POS if k in t); n=sum(1 for k in self.NEG if k in t)
            if p>n: pos+=1
            elif n>p: neg+=1
            else: neu+=1
        total=max(1,pos+neg+neu)
        disagreement=1-abs(pos-neg)/total
        return {"discussion_count":pos+neg+neu,"positive_count":pos,"negative_count":neg,"neutral_count":neu,"positive_ratio":round(pos/total,3),"negative_ratio":round(neg/total,3),"disagreement":round(disagreement,3),"rumor_risk":"高" if disagreement>0.65 and total>=5 else "中" if neg/total>0.35 else "低","basis":"社区只作为情绪、分歧和传闻风险观察，不作为公司事实。"}
