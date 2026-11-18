export interface Pokemon { id: number; nombre: string; tipo: string; tipos?: string[]; vida: number; ataque?: number; nivel?: number; estadisticas?: Record<string,number>; estadisticas_base?: Record<string,number>; experiencia_base?: number; seleccionable?: boolean; rival?: boolean; }
export interface Jugador { id: number; nombre: string; pokemon_id: number; experiencia: number; nivel?: number; pokemon_actual_id?: number; pokemon?: Pokemon; xp_nivel?: number; xp_siguiente_nivel?: number; xp_restante?: number; siguiente_evolucion_nivel?: number | null; }
export interface Movimiento { nombre: string; potencia: number; tipo: string; }
export interface EventoCombate {
  tipo: string; actor?: string; pokemon?: string; movimiento?: string;
  cantidad?: number; objetivo?: string; ps_restantes?: number; mensaje?: string;
}
export interface Combate {
  combate_id: number; jugador_id: number; pokemon_jugador: Pokemon;
  pokemon_enemigo: Pokemon; ps_jugador: number; ps_enemigo: number;
  turno: number; estado: string; mensaje: string; resultado_id?: number;
  movimientos: Movimiento[]; eventos?: EventoCombate[];
  nivel_jugador?: number; nivel_enemigo?: number; ps_max_jugador?: number; ps_max_enemigo?: number;
}
export interface EstadisticaKafka {
  jugador_id: number; victorias: number; derrotas: number;
  ataques_jugador: number; ataques_enemigo: number;
  dano_causado: number; dano_recibido: number;
  actualizado_en?: string;
}
export interface KafkaPartition {
  id: number; leader: number | null; replicas: number[];
  isr: number[]; offset_actual: number | null;
  offset_final: number | null; lag: number | null;
}
export interface KafkaTopic { name: string; partitions: KafkaPartition[]; }
export interface KafkaOverview {
  available: boolean; error?: string; brokers: number[];
  topics: KafkaTopic[]; consumer_group: string;
  generated_at: string;
}
export interface KafkaActivity {
  event_id: string; event_type: string; topic: string; player_id: number;
  status: string; created_at: string; partition: number | null;
  offset: number | null;
}
