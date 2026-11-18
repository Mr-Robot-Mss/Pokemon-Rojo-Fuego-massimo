import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Combate, Jugador, Pokemon } from '../models/game.models';

@Injectable({ providedIn: 'root' })
export class PokemonApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api';

  pokemons(): Observable<Pokemon[]> { return this.http.get<Pokemon[]>(`${this.base}/pokemon/`); }
  jugadores(): Observable<Jugador[]> { return this.http.get<Jugador[]>(`${this.base}/players/`); }
  jugador(id: number): Observable<Jugador> { return this.http.get<Jugador>(`${this.base}/players/${id}`); }
  crearJugador(nombre: string, pokemon_id: number): Observable<Jugador> {
    return this.http.post<Jugador>(`${this.base}/players/`, { nombre, pokemon_id });
  }
  iniciarCombate(jugador_id: number, pokemon_salvaje_id: number = 0): Observable<Combate> {
    return this.http.post<Combate>(`${this.base}/battles/start`, { jugador_id, pokemon_salvaje_id });
  }
  atacar(combate: Combate, movimiento: string): Observable<Combate> {
    return this.http.post<Combate>(`${this.base}/battles/${combate.combate_id}/attack`, {
      movimiento, turno_esperado: combate.turno
    });
  }
  monedas(jugadorId: number): Observable<{monedas: number}> {
    return this.http.get<{monedas: number}>(`${this.base}/rewards/player/${jugadorId}`);
  }
}
