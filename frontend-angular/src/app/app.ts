
import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

import {
  Combate,
  EstadisticaKafka,
  Jugador,
  KafkaActivity,
  KafkaOverview,
  Pokemon
} from './core/models/game.models';

import { PokemonApiService } from './core/services/pokemon-api.service';
import { KafkaMonitorService } from './core/services/kafka-monitor.service';

import { TrainerSummaryComponent } from './features/trainers/trainer-summary.component';
import { BattleLogComponent } from './features/battle/battle-log.component';
import { StatsViewComponent } from './features/statistics/stats-view.component';
import { TopicsViewComponent } from './features/kafka-monitor/topics-view.component';

type Vista = 'jugar' | 'entrenadores' | 'estadisticas' | 'topicos';
type EvolucionVisible = { anterior: string; nuevo: string; spriteAnterior: string; spriteNuevo: string; nivel: number }; 

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TrainerSummaryComponent,
    BattleLogComponent,
    StatsViewComponent,
    TopicsViewComponent
  ],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App implements OnInit, OnDestroy {

  private readonly api = inject(PokemonApiService);
  private readonly kafkaApi = inject(KafkaMonitorService);

  private monitorTimer?: ReturnType<typeof setInterval>;
  private monitorEnCurso = false;
  private evolucionTimer?: ReturnType<typeof setTimeout>;
  readonly evolucion = signal<EvolucionVisible | null>(null);

  readonly vista = signal<Vista>('jugar');
  readonly pokemons = signal<Pokemon[]>([]);
  readonly jugadores = signal<Jugador[]>([]);
  readonly jugador = signal<Jugador | null>(null);
  readonly combate = signal<Combate | null>(null);
  readonly estadisticas = signal<EstadisticaKafka | null>(null);
  readonly overview = signal<KafkaOverview | null>(null);
  readonly actividad = signal<KafkaActivity[]>([]);

  readonly apiOnline = signal(false);
  readonly cargando = signal(false);
  readonly ejecutando = signal(false);

  readonly monitorError = signal('');

  readonly mensaje = signal(
    'Selecciona un entrenador para comenzar tu aventura.'
  );

  readonly bitacora = signal<string[]>([]);
  readonly monedas = signal<number | null>(null);

  // Animaciones de impacto
  readonly animateEnemy = signal(false);
  readonly animatePlayer = signal(false);

  jugadorId = 0;
  pokemonRivalId = 0;
  pokemonInicialId = 1;
  nombreNuevo = '';

  readonly vistas: {
    id: Vista;
    texto: string;
    icono: string;
  }[] = [
    { id: 'jugar', texto: 'Jugar', icono: '🎮' },
    { id: 'entrenadores', texto: 'Entrenadores', icono: '👤' },
    { id: 'estadisticas', texto: 'Estadísticas Kafka', icono: '📊' },
    { id: 'topicos', texto: 'Tópicos (Kafka)', icono: '◈' }
  ];

  // ========================================
  // INICIALIZACIÓN
  // ========================================

  async ngOnInit(): Promise<void> {

    await this.cargarBase();
    await this.refrescarMonitor();

    this.monitorTimer = setInterval(() => {
      void this.refrescarMonitor();
    }, 10000);
  }

  ngOnDestroy(): void {

    if (this.monitorTimer) {
      clearInterval(this.monitorTimer);
    }
    if (this.evolucionTimer) {
      clearTimeout(this.evolucionTimer);
    }
  }

  seleccionarVista(vista: Vista): void {
    this.vista.set(vista);
  }

  // ========================================
  // CARGAR ENTRENADORES Y POKÉMON
  // ========================================

  async cargarBase(): Promise<void> {

    try {

      const [pokemons, jugadores] = await Promise.all([
        firstValueFrom(this.api.pokemons()),
        firstValueFrom(this.api.jugadores())
      ]);

      this.pokemons.set(pokemons);
      this.jugadores.set(jugadores);
      this.apiOnline.set(true);

      if (jugadores.length && !this.jugadorId) {

        this.jugadorId = jugadores[0].id;
        await this.seleccionarJugador();
      }

    } catch (error) {

      this.apiOnline.set(false);

      this.mensaje.set(
        'No se pudo contactar con FastAPI. Verifica el backend.'
      );

      this.agregarLog(this.errorTexto(error));
    }
  }

  // ========================================
  // CREAR ENTRENADOR
  // ========================================

  async crearJugador(): Promise<void> {

    const nombre = this.nombreNuevo.trim();

    if (!nombre) {
      this.mensaje.set('Escribe un nombre para tu entrenador.');
      return;
    }

    this.cargando.set(true);

    try {

      const nuevo = await firstValueFrom(
        this.api.crearJugador(
          nombre,
          Number(this.pokemonInicialId)
        )
      );

      this.nombreNuevo = '';

      this.jugadores.set(
        await firstValueFrom(this.api.jugadores())
      );

      this.jugadorId = nuevo.id;

      await this.seleccionarJugador();

      this.mensaje.set(
        `¡Bienvenido, ${nuevo.nombre}! Tu aventura comienza ahora.`
      );

      this.vista.set('jugar');

    } catch (error) {

      this.mensaje.set(this.errorTexto(error));

    } finally {

      this.cargando.set(false);
    }
  }

  // ========================================
  // SELECCIONAR ENTRENADOR
  // ========================================

  async seleccionarJugador(): Promise<void> {

    if (!this.jugadorId) {

      this.jugador.set(null);
      this.combate.set(null);

      return;
    }

    try {

      this.jugador.set(
        await firstValueFrom(
          this.api.jugador(Number(this.jugadorId))
        )
      );

      this.combate.set(null);

      await this.refrescarJugador();

      this.mensaje.set(
        'Inicia un combate para encontrar un Pokémon salvaje al azar.'
      );

    } catch (error) {

      this.mensaje.set(this.errorTexto(error));
    }
  }

  // ========================================
  // ACTUALIZAR ENTRENADOR
  // ========================================

  async refrescarJugador(): Promise<void> {

    const id = this.jugadorId;

    if (!id) return;

    try {

      const anterior = this.jugador();
      const actualizado = await firstValueFrom(this.api.jugador(id));
      this.jugador.set(actualizado);
      this.jugadores.update(lista => lista.map(j => j.id === actualizado.id ? actualizado : j));
      // La evolución se muestra cuando cambió la especie del entrenador activo.
      // No afecta la animación de ataques ni requiere actualizar la BD de nuevo.
      if (anterior?.id === actualizado.id && anterior.pokemon && actualizado.pokemon &&
          anterior.pokemon.id !== actualizado.pokemon.id) {
        this.evolucion.set({
          anterior: anterior.pokemon.nombre,
          nuevo: actualizado.pokemon.nombre,
          spriteAnterior: this.sprite(anterior.pokemon, 'front'),
          spriteNuevo: this.sprite(actualizado.pokemon, 'front'),
          nivel: actualizado.nivel ?? 5
        });
        if (this.evolucionTimer) clearTimeout(this.evolucionTimer);
        this.evolucionTimer = setTimeout(() => this.evolucion.set(null), 4900);
      }

    } catch {
      // Conservar datos ante error transitorio.
    }

    try {

      this.monedas.set(
        (await firstValueFrom(this.api.monedas(id))).monedas
      );

    } catch {

      this.monedas.set(null);
    }

    try {

      this.estadisticas.set(
        await firstValueFrom(this.kafkaApi.stats(id))
      );

    } catch {

      this.estadisticas.set(null);
    }
  }

  // ========================================
  // INICIAR COMBATE
  // ========================================

  async iniciarCombate(): Promise<void> {

    if (!this.jugadorId || this.ejecutando()) {
      return;
    }

    this.cargando.set(true);

    try {

      const combate = await firstValueFrom(
        this.api.iniciarCombate(
          this.jugadorId,
          0
        )
      );

      this.combate.set(combate);

      this.bitacora.set([]);

      this.mensaje.set(combate.mensaje);

      this.agregarLog(
        `Encuentro: ${combate.pokemon_jugador.nombre} vs. ${combate.pokemon_enemigo.nombre}`
      );

    } catch (error) {

      this.mensaje.set(this.errorTexto(error));

    } finally {

      this.cargando.set(false);
    }
  }

  // ========================================
  // ESPERAR ENTRE ANIMACIONES
  // ========================================

  private esperar(ms: number): Promise<void> {

    return new Promise(resolve => {
      setTimeout(resolve, ms);
    });
  }

  // ========================================
  // ATAQUE POR TURNOS
  // ========================================

  async atacar(nombre: string): Promise<void> {

    const anterior = this.combate();

    if (
      !anterior ||
      anterior.estado !== 'activo' ||
      this.ejecutando()
    ) {
      return;
    }

    // Bloqueamos nuevos ataques hasta que
    // finalice la secuencia completa.
    this.ejecutando.set(true);

    this.animatePlayer.set(false);
    this.animateEnemy.set(false);

    this.mensaje.set(`Preparando ${nombre}...`);

    try {

      // FastAPI calcula todo el turno.
      // Angular lo reproducirá visualmente
      // en orden, evento por evento.

      const siguiente = await firstValueFrom(
        this.api.atacar(anterior, nombre)
      );

      const eventos = siguiente.eventos ?? [];

      this.agregarLog(`── Turno ${anterior.turno} ──`);

      // Conservamos los puntos de salud
      // anteriores para que no bajen juntos.

      let psJugador = anterior.ps_jugador;
      let psEnemigo = anterior.ps_enemigo;

      let actorActual: string | undefined;

      this.combate.set({ ...anterior });

      // ====================================
      // REPRODUCIR EVENTOS EN SECUENCIA
      // ====================================

      for (const evento of eventos) {

        // ==================================
        // 1. ANIMACIÓN DEL ATAQUE
        // ==================================

        if (evento.tipo === 'ataque') {

          actorActual = evento.actor;

          const atacante = evento.pokemon || (
            actorActual === 'enemigo'
              ? anterior.pokemon_enemigo.nombre
              : anterior.pokemon_jugador.nombre
          );

          const movimiento = evento.movimiento
            || 'un movimiento';

          const texto = `¡${atacante} usó ${movimiento}!`;

          this.mensaje.set(texto);
          this.agregarLog(texto);

          // Si ataca el jugador,
          // el impacto ocurre en el enemigo.
          if (actorActual === 'jugador') {

            this.animateEnemy.set(true);

          } else if (actorActual === 'enemigo') {

            this.animatePlayer.set(true);
          }

          // Mostrar el ataque
          await this.esperar(280);

          // Terminar animación
          this.animateEnemy.set(false);
          this.animatePlayer.set(false);

          // Separar visualmente ambos golpes
          await this.esperar(100);

          continue;
        }

        // ==================================
        // 2. ACTUALIZAR DAÑO
        // ==================================

        if (evento.tipo === 'dano') {

          if (evento.objetivo === 'enemigo') {

            psEnemigo = evento.ps_restantes
              ?? Math.max(
                0,
                psEnemigo - (evento.cantidad ?? 0)
              );

          } else if (evento.objetivo === 'jugador') {

            psJugador = evento.ps_restantes
              ?? Math.max(
                0,
                psJugador - (evento.cantidad ?? 0)
              );
          }

          // Solamente actualizamos los PS
          // del Pokémon que recibió daño.
          this.combate.set({
            ...anterior,
            ps_jugador: psJugador,
            ps_enemigo: psEnemigo
          });

          const pokemonGolpeado =
            evento.objetivo === 'enemigo'
              ? anterior.pokemon_enemigo.nombre
              : anterior.pokemon_jugador.nombre;

          const texto =
            `${pokemonGolpeado} recibió ${evento.cantidad ?? 0} PS de daño.`;

          this.mensaje.set(texto);
          this.agregarLog(texto);

          // Dejar visible el daño
          await this.esperar(220);

          continue;
        }

        // ==================================
        // 3. MENSAJES DE EFECTIVIDAD
        // ==================================

        if (evento.mensaje) {

          this.mensaje.set(evento.mensaje);

          this.agregarLog(evento.mensaje);

          await this.esperar(
            evento.tipo === 'efectividad'
              ? 240
              : 230
          );
        }
      }

      // ====================================
      // 4. FINALIZAR EL TURNO
      // ====================================

      // El estado definitivo se muestra solo
      // al terminar todas las animaciones.

      this.combate.set(siguiente);

      if (siguiente.estado === 'victoria') {

        this.mensaje.set(
          '🏆 ¡VICTORIA! Ganaste el combate.'
        );

      } else if (siguiente.estado === 'derrota') {

        this.mensaje.set(
          '💔 Tu Pokémon se debilitó.'
        );

      } else {

        this.mensaje.set(
          '¡Elige tu siguiente movimiento!'
        );
      }

      // Actualizar experiencia y recompensas
      // si el combate ha terminado.
      if (siguiente.estado !== 'activo') {
        // El resultado ya quedó confirmado en FastAPI. EXP y evolución
        // se consultan sin mantener bloqueados los botones.
        void this.refrescarJugador();
      }

      // El monitoreo es informativo: nunca debe retrasar el siguiente turno.
      void this.refrescarMonitor();

    } catch (error) {

      this.combate.set(anterior);
      this.mensaje.set(this.errorTexto(error));

    } finally {

      // El turno vuelve a estar disponible.
      this.animatePlayer.set(false);
      this.animateEnemy.set(false);

      this.ejecutando.set(false);
    }
  }

  // ========================================
  // MONITOREO KAFKA
  // ========================================

  async refrescarMonitor(): Promise<void> {

    // Kafka puede tardar varios segundos en responder.
    // Evita solicitudes superpuestas; las batallas nunca lo esperan.
    if (this.monitorEnCurso) return;
    this.monitorEnCurso = true;
    const id = this.jugadorId;

    try {
      const [resumen, actividad, estadisticas] = await Promise.allSettled([
        firstValueFrom(this.kafkaApi.overview()),
        firstValueFrom(this.kafkaApi.activity()),
        id ? firstValueFrom(this.kafkaApi.stats(id)) : Promise.resolve(null)
      ]);

      if (resumen.status === 'fulfilled') {
        const overview = resumen.value;
        this.overview.set(overview);
        this.monitorError.set(
          overview.available ? '' : (overview.error || 'Kafka no disponible')
        );
      } else {
        this.overview.set(null);
        this.monitorError.set('Monitor Kafka no disponible.');
      }

      this.actividad.set(
        actividad.status === 'fulfilled' ? actividad.value : []
      );

      if (this.jugadorId === id) {
        this.estadisticas.set(
          estadisticas.status === 'fulfilled' ? estadisticas.value : null
        );
      }
    } finally {
      this.monitorEnCurso = false;
    }
  }

  // ========================================
  // POKÉMON DEL ENTRENADOR
  // ========================================

  iniciales(): Pokemon[] {
    return this.pokemons().filter(p => [1, 2, 3].includes(p.id));
  }

  pokemonDeJugador(): Pokemon | null {

    const jug = this.jugador();

    return jug?.pokemon
      ?? this.pokemons().find(
        p => p.id === jug?.pokemon_id
      )
      ?? null;
  }

  // ========================================
  // POKÉMON RIVAL
  // ========================================

  pokemonRival(): Pokemon | null {

    return this.combate()?.pokemon_enemigo ?? null;
  }

  // ========================================
  // SPRITES
  // ========================================

  sprite(
    p: Pokemon | null,
    vista: 'front' | 'back'
  ): string {

    const nombre = p?.nombre?.toLowerCase().trim();

    if (
      !nombre ||
      !['charmander', 'squirtle', 'bulbasaur', 'pikachu', 'snorlax', 'gengar', 'dragonite', 'gyarados', 'alakazam', 'arcanine', 'machamp', 'lapras', 'mewtwo', 'charmeleon', 'charizard', 'ivysaur', 'venusaur', 'wartortle', 'blastoise'].includes(nombre)
    ) {
      return '';
    }

    return `/sprites/${nombre}-${vista}.png`;
  }

  // ========================================
  // PORCENTAJE DE SALUD
  // ========================================

  salud(actual: number, max: number): number {

    if (max <= 0) {
      return 0;
    }

    return Math.max(
      0,
      Math.min(100, actual / max * 100)
    );
  }

  // ========================================
  // LAG DE KAFKA
  // ========================================

  lagTotal(): number | null {

    const overview = this.overview();

    if (!overview?.available) {
      return null;
    }

    const valores = overview.topics
      .flatMap(topic =>
        topic.partitions.map(p => p.lag)
      )
      .filter(
        (valor): valor is number => valor !== null
      );

    return valores.length
      ? valores.reduce((a, b) => a + b, 0)
      : null;
  }

  // ========================================
  // CANTIDAD DE EVENTOS
  // ========================================

  cantidadEventos(topic: string): number {

    return this.actividad().filter(
      evento => evento.topic === topic
    ).length;
  }

  // ========================================
  // BITÁCORA DEL COMBATE
  // ========================================

  agregarLog(texto: string): void {

    this.bitacora.update(
      anterior => [
        ...anterior.slice(-199),
        texto
      ]
    );
  }

  // ========================================
  // MANEJO DE ERRORES
  // ========================================

  errorTexto(error: unknown): string {

    const e = error as {
      error?: {
        detail?: string | { msg?: string }[]
      };
      message?: string;
    };

    const detalle = e?.error?.detail;

    if (typeof detalle === 'string') {
      return detalle;
    }

    if (Array.isArray(detalle)) {

      return detalle.map(
        item => item.msg || 'Error de validación'
      ).join('; ');
    }

    return e?.message
      || 'Ocurrió un error inesperado';
  }
}
