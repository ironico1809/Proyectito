import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { BehaviorSubject, combineLatest, map, of, shareReplay, Subscription, switchMap } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { IncidentesApi, IncidenteOut } from '../../../../infra/api/incidentes.api';
import { WebSocketService } from '../../../../infra/realtime/websocket.service';
import { SessionStore } from '../../../../infra/session/session.store';

@Component({
  selector: 'ev-incidents-page',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './incidents.page.html',
  styleUrl: './incidents.page.css',
})
export class IncidentsPage implements OnInit, OnDestroy {
  private readonly api = inject(IncidentesApi);
  private readonly wsService = inject(WebSocketService);
  private readonly session = inject(SessionStore);
  
  userRole = this.session.snapshot()?.role || '';
  pageSize = 10;
  private totalPagesValue = 1;
  private wsSub?: Subscription;

  private readonly searchSubject = new BehaviorSubject<string>('');
  private readonly filterSubject = new BehaviorSubject<string>('todas');
  private readonly pageSubject = new BehaviorSubject<number>(0);
  readonly refreshTrigger$ = new BehaviorSubject<number>(0);

  readonly searchTerm$ = this.searchSubject.asObservable();
  readonly statusFilter$ = this.filterSubject.asObservable();
  readonly currentPage$ = this.pageSubject.asObservable();

  hasNewAlert = false;
  newAlertMessage = '';

  readonly paginationInfo$ = combineLatest([
    this.pageSubject,
    this.filterSubject,
    this.searchSubject,
    this.refreshTrigger$
  ]).pipe(
    switchMap(([page, filter, search]) =>
      this.api.listarTodos(page + 1, this.pageSize, filter, search).pipe(
        catchError(() => of({ items: [], total: 0, page: page + 1, pages: 1 }))
      )
    ),
    shareReplay(1)
  );

  readonly paged$ = this.paginationInfo$.pipe(
    map((res) => res.items)
  );

  readonly totalPages$ = this.paginationInfo$.pipe(
    map((res) => {
      this.totalPagesValue = res.pages;
      return res.pages;
    })
  );

  readonly totalItems$ = this.paginationInfo$.pipe(
    map((res) => res.total)
  );

  ngOnInit(): void {
    this.wsService.connectGlobal();
    this.wsSub = this.wsService.messages$.subscribe((msg) => {
      if (msg['tipo'] === 'nuevo_incidente') {
        this.hasNewAlert = true;
        this.newAlertMessage = `🚨 Nueva emergencia #${msg['id_incidente']} (${msg['prioridad'] || 'pendiente'})`;
        this.refreshList();
        // Auto-hide alert after 8 seconds
        setTimeout(() => { this.hasNewAlert = false; }, 8000);
      } else if (msg['tipo'] === 'cambio_estado') {
        this.refreshList();
      }
    });
  }

  refreshList(): void {
    this.refreshTrigger$.next(this.refreshTrigger$.value + 1);
  }

  setFilter(filter: string) {
    this.filterSubject.next(filter);
    this.pageSubject.next(0);
  }

  onSearch(term: string) {
    this.searchSubject.next(term);
    this.pageSubject.next(0);
  }

  goToPage(page: number) {
    this.pageSubject.next(page);
  }

  prevPage() {
    const current = this.pageSubject.value;
    if (current > 0) this.pageSubject.next(current - 1);
  }

  nextPage() {
    const current = this.pageSubject.value;
    if (current < this.totalPagesValue - 1) this.pageSubject.next(current + 1);
  }

  formatDate(ts: string): string {
    const d = new Date(ts);
    return d.toLocaleDateString('es-BO', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  trackById(_: number, item: IncidenteOut) {
    return item.id_incidente;
  }

  ngOnDestroy(): void {
    this.wsSub?.unsubscribe();
    this.wsService.disconnect();
  }
}
