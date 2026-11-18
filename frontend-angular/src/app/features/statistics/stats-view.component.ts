import { Component, EventEmitter, Input, Output } from '@angular/core';
import { EstadisticaKafka, KafkaActivity } from '../../core/models/game.models';

@Component({
  selector: 'app-stats-view',
  standalone: true,
  template: `
    <section class="panel content-panel">
      <h2>📊 Estadísticas Kafka</h2>
      <div class="content-inner">
        <p>Datos derivados de los eventos procesados por Kafka y almacenados en PostgreSQL.</p>
        <button type="button" class="subtle-button" (click)="refresh.emit()">↻ Actualizar métricas</button>
        <div class="metric-grid">
          <div><small>🏆 Victorias</small><strong>{{ stats?.victorias ?? '—' }}</strong></div>
          <div><small>☠️ Derrotas</small><strong>{{ stats?.derrotas ?? '—' }}</strong></div>
          <div><small>⚔️ Ataques propios</small><strong>{{ stats?.ataques_jugador ?? '—' }}</strong></div>
          <div><small>🛡️ Ataques enemigos</small><strong>{{ stats?.ataques_enemigo ?? '—' }}</strong></div>
          <div><small>💥 Daño causado</small><strong>{{ stats?.dano_causado ?? '—' }}</strong></div>
          <div><small>💔 Daño recibido</small><strong>{{ stats?.dano_recibido ?? '—' }}</strong></div>
        </div>
        <h3>Eventos recientes del Outbox</h3>
        <div class="event-list">
          @for (event of activity; track event.event_id) {
            <div><strong>{{event.event_type}}</strong><span>{{event.topic}}</span><small>Jugador {{event.player_id}} · {{event.status}} · offset {{event.offset ?? '—'}}</small></div>
          } @empty { <p>No hay eventos disponibles; revisa el endpoint de monitoreo.</p> }
        </div>
        <p class="muted">El historial del Outbox no representa todo el historial retenido en Kafka.</p>
      </div>
    </section>
  `,
  styles: [`
    .panel { overflow: hidden; background: #fff8eb; border: 2px solid #911c28; border-radius: 12px; }
    h2 { margin: 0; background: #af1b2b; color: #fff; padding: 14px 18px; font-size: 20px; }
    .content-inner { padding: 18px; }
    button { padding: 10px 14px; border: 1px solid #a92132; border-radius: 8px; background: white; color: #8b1c2a; font-weight: bold; cursor: pointer; }
    .metric-grid { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 12px; margin-top: 18px; }
    .metric-grid div { border: 1px solid #ddc3aa; background: #fffdf4; border-radius: 9px; padding: 14px; }
    .metric-grid small,.metric-grid strong { display: block; }
    .metric-grid strong { font-size: 28px; margin-top: 8px; }
    .event-list { display: grid; gap: 8px; }
    .event-list div { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 6px; padding: 10px; background: #f6ead9; border-radius: 7px; }
    .muted { color: #796c68; font-size: 12px; }
    @media(max-width:600px){ .metric-grid { grid-template-columns: repeat(2,minmax(0,1fr)); } }
  `]
})
export class StatsViewComponent {
  @Input() stats: EstadisticaKafka | null = null;
  @Input() activity: KafkaActivity[] = [];
  @Output() refresh = new EventEmitter<void>();
}
