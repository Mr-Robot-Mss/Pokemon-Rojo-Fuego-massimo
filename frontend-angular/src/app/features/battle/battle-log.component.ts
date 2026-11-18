import { AfterViewChecked, Component, ElementRef, Input, ViewChild } from '@angular/core';

@Component({
  selector: 'app-battle-log',
  standalone: true,
  template: `
    <div #registro class="entries" role="log" aria-label="Registro del combate" aria-live="polite" tabindex="0">
      @for (entry of entries; track $index) {
        <div class="entry" [class.turn]="entry.startsWith('── Turno')"
             [class.attack]="entry.includes('usó')"
             [class.important]="entry.includes('debilitó') || entry.includes('experiencia') || entry.includes('EXP')">
          <span class="index">{{ $index + 1 }}</span><span>{{ entry }}</span>
        </div>
      } @empty {
        <small>Inicia un combate. Aquí aparecerán los turnos, movimientos, daños y efectos.</small>
      }
    </div>
  `,
  styles: [`
    /* Solo esta sección se desplaza: el juego no crece infinitamente. */
    :host { display:block; width:100%; height:100%; min-height:0; }
    .entries {
      height:100%; max-height:none; min-height:0;
      overflow-y:auto; overflow-x:hidden; overscroll-behavior:contain;
      display:grid; align-content:start; gap:3px;
      padding:2px 5px 2px 0; font-size:12px; line-height:1.35;
      scrollbar-width:thin; scrollbar-color:#bd2339 #fff5e5;
    }
    .entries:focus-visible {outline:2px solid #bd2339; outline-offset:2px;}
    .entry {display:flex;align-items:flex-start;gap:7px;min-width:0;background:#fffdf7;border-bottom:1px solid #ead6be;padding:5px 4px;border-radius:5px;}
    .entry span:last-child {min-width:0;overflow-wrap:anywhere;}
    .entry.turn{background:#e2d5fb;color:#542b82;font-weight:900;border-top:1px solid #ab91db;}
    .entry.attack{background:#fff0e0;font-weight:800;color:#a21c2c;}
    .entry.important{background:#eaf8df;font-weight:800;}
    .index{font-size:10px;color:#8e7d6d;flex:0 0 18px;text-align:right;padding-top:1px;}
    small { color:#82746a; }
  `]
})
export class BattleLogComponent implements AfterViewChecked {
  @Input() entries: string[] = [];
  @ViewChild('registro') private registro?: ElementRef<HTMLDivElement>;
  private ultimoTamano = -1;

  ngAfterViewChecked(): void {
    if (this.entries.length === this.ultimoTamano) return;
    this.ultimoTamano = this.entries.length;
    // Al agregar un movimiento se muestra el último mensaje, no el primero.
    const elemento = this.registro?.nativeElement;
    if (elemento) elemento.scrollTop = elemento.scrollHeight;
  }
}
