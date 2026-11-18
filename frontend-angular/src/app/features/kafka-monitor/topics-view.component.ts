import { Component, EventEmitter, Input, Output } from '@angular/core';
import { KafkaOverview } from '../../core/models/game.models';
import { StatusIndicatorComponent } from '../../shared/components/status-indicator/status-indicator.component';

@Component({
  selector: 'app-topics-view',
  standalone: true,
  imports: [StatusIndicatorComponent],
  template: `
    <section class="panel content-panel">
      <h2>◈ Tópicos y brokers Kafka</h2>
      <div class="content-inner">
        <div class="toolbar">
          <app-status-indicator [online]="overview?.available ?? false" onlineText="Kafka disponible" offlineText="Kafka sin verificar" />
          <button type="button" (click)="refresh.emit()">↻ Actualizar</button>
        </div>
        @if (error) { <p class="warning">{{error}}</p> }
        <div class="metrics">
          <div><small>Brokers detectados</small><strong>{{overview?.available ? overview?.brokers?.length : '—'}}</strong></div>
          <div><small>Tópicos</small><strong>{{overview?.topics?.length ?? '—'}}</strong></div>
          <div><small>Lag total conocido</small><strong>{{lagTotal() ?? '—'}}</strong></div>
        </div>
        @for (topic of overview?.topics ?? []; track topic.name) {
          <article class="topic">
            <h3>{{topic.name}}</h3>
            <p>Particiones: {{topic.partitions.length}} · Replicación configurada: {{topic.partitions[0]?.replicas?.length ?? '—'}}</p>
            <div class="scroll"><table><thead><tr><th>Partición</th><th>Líder</th><th>Réplicas</th><th>ISR</th><th>Offset</th><th>Log-end</th><th>Lag</th></tr></thead>
              <tbody>@for (part of topic.partitions; track part.id) {
                <tr><td>{{part.id}}</td><td>{{part.leader ?? '—'}}</td><td>{{part.replicas.join(', ')}}</td><td>{{part.isr.join(', ')}}</td><td>{{part.offset_actual ?? '—'}}</td><td>{{part.offset_final ?? '—'}}</td><td>{{part.lag ?? '—'}}</td></tr>
              }</tbody>
            </table></div>
          </article>
        } @empty { <p>Sin datos de tópicos. Verifica la conexión con el router de monitoreo de FastAPI.</p> }
        <p class="muted">Consumer group: {{ overview?.consumer_group || 'pokemon-massimo-analytics-v1' }}</p>
        <p class="muted">Lag desconocido se muestra como «—», nunca se interpreta como cero.</p>
        <a href="http://localhost:8085" target="_blank" rel="noopener noreferrer">Abrir Kafka UI ↗</a>
      </div>
    </section>
  `,
  styles: [`
    .panel { overflow: hidden; background:#fff8eb; border:2px solid #911c28; border-radius:12px; }
    h2 { margin:0; background:#af1b2b; color:white; padding:14px 18px; font-size:20px; }
    .content-inner { padding:18px; }
    .toolbar { display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:10px; }
    button { padding:10px; background:#fff; color:#99202e; border:1px solid #99202e; border-radius:8px; cursor:pointer; }
    .metrics { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin:18px 0; }
    .metrics div { background:#f5e6d0; border:1px solid #dbc0a1; border-radius:9px; padding:12px; }
    .metrics small,.metrics strong {display:block;}
    .metrics strong {font-size:26px;margin-top:6px;}
    .topic { margin:15px 0; padding:12px; background:#fffdf6; border:1px solid #d9c2aa; border-radius:9px; }
    .topic h3 { overflow-wrap:anywhere; }
    .scroll { overflow-x:auto; }
    table { border-collapse:collapse; width:100%; min-width:560px; font-size:13px; }
    th,td { padding:9px; border-bottom:1px solid #e5d3bc; text-align:left; }
    .warning { color:#a12d20; } .muted { color:#736968; font-size:12px; }
    @media(max-width:600px){ .metrics {grid-template-columns:1fr;} }
  `]
})
export class TopicsViewComponent {
  @Input() overview: KafkaOverview | null = null;
  @Input() error = '';
  @Output() refresh = new EventEmitter<void>();
  lagTotal(): number | null {
    if (!this.overview?.available) return null;
    const valores = this.overview.topics.flatMap(t => t.partitions.map(p=>p.lag)).filter((v): v is number => v !== null);
    return valores.length ? valores.reduce((sum,v)=>sum+v,0) : null;
  }
}
