import { Component, Input } from '@angular/core';
import { Jugador } from '../../core/models/game.models';

@Component({
  selector: 'app-trainer-summary',
  standalone: true,
  template: `<div class="trainer-mini"><span class="avatar" aria-hidden="true">🧢</span><div><strong>{{ jugador?.nombre || 'Sin entrenador' }}</strong><small>ID: {{ jugador?.id ?? '—' }}</small></div></div>`,
  styles: [`
    .trainer-mini { display: flex; align-items: center; gap: 12px; }
    .trainer-mini strong { display: block; font-size: 16px; }
    .trainer-mini small { display: block; margin-top: 4px; color: #6d6260; }
    .avatar { display: inline-flex; align-items: center; justify-content: center; font-size: 32px; width: 52px; height: 52px; border-radius: 10px; background: #f4dfc1; }
  `]
})
export class TrainerSummaryComponent { @Input() jugador: Jugador | null = null; }
