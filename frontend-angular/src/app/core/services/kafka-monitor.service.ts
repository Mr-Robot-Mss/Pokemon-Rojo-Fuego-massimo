import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { EstadisticaKafka, KafkaActivity, KafkaOverview } from '../models/game.models';

@Injectable({ providedIn: 'root' })
export class KafkaMonitorService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/kafka';
  overview(): Observable<KafkaOverview> { return this.http.get<KafkaOverview>(`${this.base}/overview`); }
  activity(): Observable<KafkaActivity[]> { return this.http.get<KafkaActivity[]>(`${this.base}/activity`); }
  stats(id: number): Observable<EstadisticaKafka> { return this.http.get<EstadisticaKafka>(`${this.base}/stats/${id}`); }
}
