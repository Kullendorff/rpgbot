"""
Statistik visualisering för EON Discord Bot.
Genererar grafer och diagramm för tärningsstatistik med matplotlib.
"""

import os
import io
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

class StatsVisualizer:
    """Hanterar generering av statistik visualiseringar."""
    
    def __init__(self):
        # Konfigurera matplotlib för headless användning
        plt.style.use('default')
        plt.rcParams.update({
            'figure.facecolor': '#2f3136',  # Discord dark theme bakgrund
            'axes.facecolor': '#36393f',
            'axes.edgecolor': '#ffffff',
            'axes.labelcolor': '#ffffff',
            'text.color': '#ffffff',
            'xtick.color': '#ffffff',
            'ytick.color': '#ffffff',
            'grid.color': '#40444b',
            'font.size': 10
        })
        
        # Cache för genererade grafer (5 minuter)
        self.cache = {}
        self.cache_timeout = 300  # 5 minuter
    
    def _get_cache_key(self, visualization_type: str, data_hash: str) -> str:
        """Generera cache nyckel."""
        return f"{visualization_type}_{data_hash}_{int(time.time() // self.cache_timeout)}"
    
    def _save_plot_to_bytes(self, fig) -> io.BytesIO:
        """Spara matplotlib plot till bytes för Discord attachment."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', facecolor='#2f3136', edgecolor='none', 
                   bbox_inches='tight', dpi=100)
        buf.seek(0)
        plt.close(fig)
        return buf
    
    def generate_dice_distribution(self, dice_data: Dict[str, Any]) -> Optional[io.BytesIO]:
        """
        Generera tärningsfördelning histogram.
        
        Args:
            dice_data: Dict med tärningsdata innehållande:
                - rolls: List av individuella slag
                - sides: Antal sidor på tärningen
                - total_rolls: Totalt antal slag
        
        Returns:
            BytesIO buffer med PNG-bild eller None vid fel
        """
        try:
            rolls = dice_data.get('rolls', [])
            sides = dice_data.get('sides', 6)
            
            if not rolls:
                return None
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            fig.suptitle('🎲 Tärningsfördelning', fontsize=16, color='white')
            
            # Histogram av resultat
            counts, bins = np.histogram(rolls, bins=range(1, sides + 2))
            expected = len(rolls) / sides
            
            bars = ax1.bar(range(1, sides + 1), counts, alpha=0.7, 
                          color='#7289da', edgecolor='white')
            ax1.axhline(y=expected, color='red', linestyle='--', 
                       label=f'Förväntat: {expected:.1f}')
            
            ax1.set_xlabel('Tärningsvärde')
            ax1.set_ylabel('Antal slag')
            ax1.set_title('Fördelning av slag')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Lägg till värden på bars
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{count}', ha='center', va='bottom')
            
            # Kumulativ fördelning
            cumulative = np.cumsum(counts)
            ax2.plot(range(1, sides + 1), cumulative, 'o-', color='#43b581', linewidth=2)
            ax2.fill_between(range(1, sides + 1), cumulative, alpha=0.3, color='#43b581')
            
            ax2.set_xlabel('Tärningsvärde')
            ax2.set_ylabel('Kumulativa slag')
            ax2.set_title('Kumulativ fördelning')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            return self._save_plot_to_bytes(fig)
            
        except Exception as e:
            print(f"[VISUALIZATION] Fel vid generering av tärningsfördelning: {e}")
            return None
    
    def generate_activity_heatmap(self, activity_data: Dict[str, Any]) -> Optional[io.BytesIO]:
        """
        Generera aktivitets heatmap över tid.
        
        Args:
            activity_data: Dict med aktivitetsdata:
                - hourly_activity: Dict med timme -> antal aktiviteter
                - daily_activity: Dict med dag -> antal aktiviteter
        
        Returns:
            BytesIO buffer med PNG-bild
        """
        try:
            hourly = activity_data.get('hourly_activity', {})
            
            if not hourly:
                return None
            
            # Skapa 24-timmars data (fyll tomma timmar med 0)
            hours = list(range(24))
            activity = [hourly.get(str(h), 0) for h in hours]
            
            fig, ax = plt.subplots(figsize=(12, 6))
            fig.suptitle('📊 Aktivitetsmönster över dygnet', fontsize=16, color='white')
            
            # Skapa heatmap-style bar chart
            colors = plt.cm.plasma(np.linspace(0, 1, len(activity)))
            bars = ax.bar(hours, activity, color=colors, alpha=0.8)
            
            # Lägg till värden på bars
            for bar, act in zip(bars, activity):
                if act > 0:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                           f'{act}', ha='center', va='bottom', fontsize=8)
            
            ax.set_xlabel('Timme på dygnet')
            ax.set_ylabel('Antal aktiviteter')
            ax.set_xticks(range(0, 24, 2))
            ax.set_xticklabels([f'{h:02d}:00' for h in range(0, 24, 2)])
            ax.grid(True, alpha=0.3)
            
            # Markera peak hours
            max_activity = max(activity)
            peak_hours = [h for h, a in enumerate(activity) if a == max_activity]
            
            if peak_hours:
                ax.axvspan(min(peak_hours) - 0.5, max(peak_hours) + 0.5, 
                          alpha=0.2, color='yellow', label='Peak aktivitet')
                ax.legend()
            
            plt.tight_layout()
            return self._save_plot_to_bytes(fig)
            
        except Exception as e:
            print(f"[VISUALIZATION] Fel vid generering av aktivitets heatmap: {e}")
            return None
    
    def generate_success_rate_comparison(self, player_data: List[Dict[str, Any]]) -> Optional[io.BytesIO]:
        """
        Generera jämförelse av framgångsfrekvens mellan spelare.
        
        Args:
            player_data: Lista av spelardata med name, success_rate, total_rolls
        
        Returns:
            BytesIO buffer med PNG-bild
        """
        try:
            if not player_data:
                return None
            
            # Sortera spelare efter framgångsfrekvens
            sorted_players = sorted(player_data, key=lambda x: x.get('success_rate', 0), reverse=True)
            
            names = [p.get('name', 'Unknown')[:15] for p in sorted_players[:10]]  # Max 10 spelare
            success_rates = [p.get('success_rate', 0) for p in sorted_players[:10]]
            total_rolls = [p.get('total_rolls', 0) for p in sorted_players[:10]]
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            fig.suptitle('🏆 Spelarjämförelse - Framgångsfrekvens', fontsize=16, color='white')
            
            # Framgångsfrekvens bar chart
            colors = ['#ffd700' if i < 3 else '#7289da' for i in range(len(names))]
            bars1 = ax1.barh(names, success_rates, color=colors, alpha=0.8)
            
            # Lägg till procent-labels
            for bar, rate in zip(bars1, success_rates):
                width = bar.get_width()
                ax1.text(width + 0.5, bar.get_y() + bar.get_height()/2, 
                        f'{rate:.1f}%', ha='left', va='center')
            
            ax1.set_xlabel('Framgångsfrekvens (%)')
            ax1.set_title('Framgångsfrekvens per spelare')
            ax1.grid(True, alpha=0.3, axis='x')
            
            # Aktivitetsnivå (antal slag)
            bars2 = ax2.barh(names, total_rolls, color='#43b581', alpha=0.8)
            
            # Lägg till slag-labels
            for bar, rolls in zip(bars2, total_rolls):
                width = bar.get_width()
                ax2.text(width + max(total_rolls) * 0.01, bar.get_y() + bar.get_height()/2, 
                        f'{rolls}', ha='left', va='center')
            
            ax2.set_xlabel('Totalt antal slag')
            ax2.set_title('Aktivitetsnivå per spelare')
            ax2.grid(True, alpha=0.3, axis='x')
            
            plt.tight_layout()
            return self._save_plot_to_bytes(fig)
            
        except Exception as e:
            print(f"[VISUALIZATION] Fel vid generering av spelarjämförelse: {e}")
            return None
    
    def generate_skill_progression(self, progression_data: Dict[str, Any]) -> Optional[io.BytesIO]:
        """
        Generera färdighets progression curve.
        
        Args:
            progression_data: Dict med progressionsdata:
                - dates: Lista av datum
                - success_rates: Lista av framgångsfrekvenser över tid
                - roll_counts: Lista av antal slag per period
        
        Returns:
            BytesIO buffer med PNG-bild
        """
        try:
            dates = progression_data.get('dates', [])
            success_rates = progression_data.get('success_rates', [])
            roll_counts = progression_data.get('roll_counts', [])
            
            if not all([dates, success_rates, roll_counts]):
                return None
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
            fig.suptitle('📈 Färdighets Progression över Tid', fontsize=16, color='white')
            
            # Konvertera dates till datetime om de är strings
            if isinstance(dates[0], str):
                dates = [datetime.fromisoformat(d.replace('Z', '+00:00')) for d in dates]
            
            # Framgångsfrekvens över tid
            ax1.plot(dates, success_rates, 'o-', color='#7289da', linewidth=2, markersize=4)
            ax1.fill_between(dates, success_rates, alpha=0.3, color='#7289da')
            
            # Trend line
            if len(success_rates) > 2:
                z = np.polyfit(range(len(success_rates)), success_rates, 1)
                p = np.poly1d(z)
                ax1.plot(dates, p(range(len(success_rates))), "--", color='red', 
                        label=f'Trend: {"↗" if z[0] > 0 else "↘"} {abs(z[0]):.2f}%/period')
                ax1.legend()
            
            ax1.set_ylabel('Framgångsfrekvens (%)')
            ax1.set_title('Framgång över tid')
            ax1.grid(True, alpha=0.3)
            
            # Aktivitetsnivå över tid
            ax2.bar(dates, roll_counts, color='#43b581', alpha=0.7, width=0.8)
            ax2.set_ylabel('Antal slag')
            ax2.set_title('Aktivitetsnivå över tid')
            ax2.grid(True, alpha=0.3)
            
            # Formatera x-axis
            plt.xticks(rotation=45)
            plt.tight_layout()
            return self._save_plot_to_bytes(fig)
            
        except Exception as e:
            print(f"[VISUALIZATION] Fel vid generering av progression curve: {e}")
            return None
    
    def generate_command_usage_pie(self, command_data: Dict[str, int]) -> Optional[io.BytesIO]:
        """
        Generera pie chart över kommandoanvändning.
        
        Args:
            command_data: Dict med command_name -> usage_count
        
        Returns:
            BytesIO buffer med PNG-bild
        """
        try:
            if not command_data:
                return None
            
            # Ta top 8 kommandon (för läsbarhet)
            sorted_commands = sorted(command_data.items(), key=lambda x: x[1], reverse=True)[:8]
            
            commands, counts = zip(*sorted_commands)
            
            fig, ax = plt.subplots(figsize=(10, 8))
            fig.suptitle('🎮 Kommandoanvändning Fördelning', fontsize=16, color='white')
            
            # Färgschema
            colors = plt.cm.Set3(np.linspace(0, 1, len(commands)))
            
            # Skapa pie chart
            wedges, texts, autotexts = ax.pie(counts, labels=commands, colors=colors, 
                                             autopct='%1.1f%%', startangle=90,
                                             textprops={'color': 'white'})
            
            # Förbättra text läsbarhet
            for autotext in autotexts:
                autotext.set_color('black')
                autotext.set_fontweight('bold')
            
            # Lägg till legend med counts
            legend_labels = [f'{cmd}: {count} användningar' for cmd, count in sorted_commands]
            ax.legend(wedges, legend_labels, title="Kommandon", loc="center left", 
                     bbox_to_anchor=(1, 0, 0.5, 1))
            
            plt.tight_layout()
            return self._save_plot_to_bytes(fig)
            
        except Exception as e:
            print(f"[VISUALIZATION] Fel vid generering av kommando pie chart: {e}")
            return None
    
    async def generate_comprehensive_report(self, stats_data: Dict[str, Any]) -> Optional[List[io.BytesIO]]:
        """
        Generera omfattande visuell rapport med flera grafer.
        
        Args:
            stats_data: Komplett statistikdata
        
        Returns:
            Lista av BytesIO buffers eller None
        """
        try:
            images = []
            
            # Generera olika visualiseringar baserat på tillgänglig data
            if stats_data.get('dice_distribution'):
                img = self.generate_dice_distribution(stats_data['dice_distribution'])
                if img:
                    images.append(img)
            
            if stats_data.get('activity_pattern'):
                img = self.generate_activity_heatmap(stats_data['activity_pattern'])
                if img:
                    images.append(img)
            
            if stats_data.get('player_comparison'):
                img = self.generate_success_rate_comparison(stats_data['player_comparison'])
                if img:
                    images.append(img)
            
            if stats_data.get('progression'):
                img = self.generate_skill_progression(stats_data['progression'])
                if img:
                    images.append(img)
            
            if stats_data.get('command_usage'):
                img = self.generate_command_usage_pie(stats_data['command_usage'])
                if img:
                    images.append(img)
            
            return images if images else None
            
        except Exception as e:
            print(f"[VISUALIZATION] Fel vid generering av omfattande rapport: {e}")
            return None


# Convenience functions för enkel användning
async def create_dice_chart(roll_data: List[int], sides: int = 6) -> Optional[io.BytesIO]:
    """Skapa snabb tärnings-chart."""
    visualizer = StatsVisualizer()
    dice_data = {
        'rolls': roll_data,
        'sides': sides,
        'total_rolls': len(roll_data)
    }
    return visualizer.generate_dice_distribution(dice_data)

async def create_player_comparison(players: List[Dict[str, Any]]) -> Optional[io.BytesIO]:
    """Skapa snabb spelar-jämförelse chart."""
    visualizer = StatsVisualizer()
    return visualizer.generate_success_rate_comparison(players)