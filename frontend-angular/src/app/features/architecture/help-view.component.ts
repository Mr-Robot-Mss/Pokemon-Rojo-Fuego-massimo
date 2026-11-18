import { Component } from '@angular/core';

@Component({
  selector: 'app-help-view',
  standalone: true,
  template: `
    <section class="panel">
      <h2>📖 Guía de demostración Kafka</h2>
      <div class="inner">
        <h3>Flujo del evento</h3>
        <div class="steps"><span>🎮 Combate</span><span>→</span><span>FastAPI</span><span>→</span><span>PostgreSQL Outbox</span><span>→</span><span>Kafka</span><span>→</span><span>Consumer</span><span>→</span><span>Estadísticas</span></div>
        <h3>Qué explicar al profesor</h3>
        <ol>
          <li>3 nodos ZooKeeper y 3 brokers; coordinación y tolerancia a fallos.</li>
          <li>2 tópicos con 3 particiones y 3 réplicas cada uno.</li>
          <li>Eventos JSON con event_id, tipo, versión, fecha, jugador y datos.</li>
          <li>Transactional Outbox: no perder eventos cuando Kafka no responde.</li>
          <li>Consumer groups, confirmación de offsets y prevención de duplicados.</li>
          <li>Monitoreo de lag, líderes, ISR y réplicas en Kafka UI y CLI.</li>
          <li>Prueba de detención y recuperación de un broker.</li>
        </ol>
        <p class="note">Otros requisitos de la rúbrica: API Manager, JWT, OAuth/OIDC, nube y RabbitMQ. Esta interfaz por sí sola no acredita su implementación.</p>
      </div>
    </section>
  `,
  styles: [`
    .panel {overflow:hidden;background:#fff8eb;border:2px solid #911c28;border-radius:12px;}
    h2 {margin:0;background:#af1b2b;color:#fff;padding:14px 18px;font-size:20px;}
    .inner {padding:20px;line-height:1.7;}
    .steps {display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:12px 0 20px;}
    .steps span {background:#f2e1c9;border-radius:7px;padding:7px 10px;font-weight:bold;}
    .note {padding:12px;border-left:4px solid #cb8423;background:#fff0d7;}
  `]
})
export class HelpViewComponent {}
