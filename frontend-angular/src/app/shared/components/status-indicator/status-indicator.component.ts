import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-status-indicator',
  standalone: true,
  template: `<span class="indicator" [class.ok]="online"><span aria-hidden="true">●</span> {{ online ? onlineText : offlineText }}</span>`,
  styles: [`
    .indicator { display: inline-flex; align-items: center; gap: 7px; padding: 8px 12px; border-radius: 8px; background: #f2e3d0; color: #7b3030; font-weight: 800; }
    .indicator.ok { background: #d6f4d7; color: #22643b; }
  `]
})
export class StatusIndicatorComponent {
  @Input() online = false;
  @Input() onlineText = 'Conectado';
  @Input() offlineText = 'Sin verificar';
}
