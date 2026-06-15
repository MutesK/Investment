"""
백테스트 결과 시각화
"""
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from backtest.vr_models import VRBacktestResult


class VRVisualizer:
    """VR 백테스트 결과 시각화"""
    
    def __init__(self, result: VRBacktestResult):
        self.result = result
    
    def create_chart(self) -> str:
        """인터랙티브 차트 생성 (HTML)"""
        if not self.result.daily_data:
            return "<p>데이터가 없습니다.</p>"
        
        # 데이터 추출
        dates = [d.date for d in self.result.daily_data]
        evaluations = [d.evaluation for d in self.result.daily_data]
        v_values = [d.v_value for d in self.result.daily_data]
        pools = [d.pool for d in self.result.daily_data]
        min_bands = [d.min_band for d in self.result.daily_data]
        max_bands = [d.max_band for d in self.result.daily_data]
        
        # 매매 신호
        buy_dates = [d.date for d in self.result.daily_data if d.action == "buy"]
        buy_evals = [self.result.daily_data[i].evaluation for i, d in enumerate(self.result.daily_data) if d.action == "buy"]
        
        sell_dates = [d.date for d in self.result.daily_data if d.action == "sell"]
        sell_evals = [self.result.daily_data[i].evaluation for i, d in enumerate(self.result.daily_data) if d.action == "sell"]
        
        # Subplot 생성
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.12,
            row_heights=[0.7, 0.3],
            specs=[
                [{"secondary_y": True}],
                [{"secondary_y": False}]
            ]
        )
        
        # 1번 행: 평가금, 밴드, V값
        # 최대 밴드 (투명)
        fig.add_trace(
            go.Scatter(
                x=dates, y=max_bands,
                fill=None,
                mode='lines',
                line_color='rgba(0,0,0,0)',
                showlegend=False,
                name='Max Band'
            ),
            row=1, col=1, secondary_y=False
        )
        
        # 최소 밴드와의 채우기
        fig.add_trace(
            go.Scatter(
                x=dates, y=min_bands,
                fill='tonexty',
                mode='lines',
                line_color='rgba(0,0,0,0)',
                fillcolor='rgba(0,255,0,0.1)',
                showlegend=True,
                name='Band (±' + f'{self.result.config.band_rate*100:.0f}%' + ')',
                hoverinfo='skip'
            ),
            row=1, col=1, secondary_y=False
        )
        
        # V값 (주황색 실선)
        fig.add_trace(
            go.Scatter(
                x=dates, y=v_values,
                mode='lines',
                line=dict(color='orange', width=2),
                name='V (Guide Value)',
                hovertemplate='%{x}<br>V: %{y:,.0f}<extra></extra>'
            ),
            row=1, col=1, secondary_y=False
        )
        
        # 평가금 (빨간색)
        fig.add_trace(
            go.Scatter(
                x=dates, y=evaluations,
                mode='lines',
                line=dict(color='red', width=2),
                name='Evaluation',
                hovertemplate='%{x}<br>Evaluation: %{y:,.0f}<extra></extra>'
            ),
            row=1, col=1, secondary_y=False
        )
        
        # 매수 신호 (초록색 화살표)
        if buy_dates:
            fig.add_trace(
                go.Scatter(
                    x=buy_dates, y=buy_evals,
                    mode='markers',
                    marker=dict(size=10, color='green', symbol='triangle-up'),
                    name='Buy',
                    hovertemplate='%{x}<br>Buy<extra></extra>'
                ),
                row=1, col=1, secondary_y=False
            )
        
        # 매도 신호 (빨간색 화살표)
        if sell_dates:
            fig.add_trace(
                go.Scatter(
                    x=sell_dates, y=sell_evals,
                    mode='markers',
                    marker=dict(size=10, color='darkred', symbol='triangle-down'),
                    name='Sell',
                    hovertemplate='%{x}<br>Sell<extra></extra>'
                ),
                row=1, col=1, secondary_y=False
            )
        
        # 2번 행: Pool (파란색)
        fig.add_trace(
            go.Scatter(
                x=dates, y=pools,
                mode='lines',
                line=dict(color='blue', width=2),
                name='Pool',
                hovertemplate='%{x}<br>Pool: %{y:,.0f}<extra></extra>'
            ),
            row=2, col=1, secondary_y=False
        )
        
        # 레이아웃 설정
        fig.update_layout(
            title=dict(
                text=f"VR Backtest - {self.result.config.vr_type.upper()}<br>" +
                     f"Return: {self.result.total_return*100:.2f}% | Annual: {self.result.annual_return*100:.2f}% | Max DD: {self.result.max_drawdown*100:.2f}%",
                x=0.5,
                xanchor='center'
            ),
            hovermode='x unified',
            height=800,
            template='plotly_white'
        )
        
        # X축 레이블
        fig.update_xaxes(title_text="Date", row=2, col=1)
        
        # Y축 레이블
        fig.update_yaxes(title_text="Price ($)", row=1, col=1, secondary_y=False)
        fig.update_yaxes(title_text="Pool ($)", row=2, col=1, secondary_y=False)
        
        return json.loads(fig.to_json())
    
    def get_summary(self) -> dict:
        """요약 통계"""
        return {
            "config_type": self.result.config.vr_type,
            "initial_capital": f"${self.result.config.initial_capital:,.0f}",
            "final_evaluation": f"${self.result.daily_data[-1].evaluation:,.0f}" if self.result.daily_data else "$0",
            "total_return": f"{self.result.total_return*100:.2f}%",
            "annual_return": f"{self.result.annual_return*100:.2f}%",
            "max_drawdown": f"{self.result.max_drawdown*100:.2f}%",
            "total_trades": self.result.total_trades,
            "final_pool": f"${self.result.daily_data[-1].pool:,.0f}" if self.result.daily_data else "$0",
            "final_shares": f"{self.result.daily_data[-1].shares:,.2f}" if self.result.daily_data else "0",
        }
