import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'ev-history-page',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './history.page.html',
  styleUrl: './history.page.css',
})
export class HistoryPage {
  records = [
    { id: '1023', date: '2026-06-03', client: 'María Fernández', vehicle: 'Toyota Corolla 2018', mechanic: 'Jorge Pérez', status: 'Finalizado' },
    { id: '1019', date: '2026-06-01', client: 'Carlos López', vehicle: 'Nissan Sentra 2015', mechanic: 'Luis Gómez', status: 'Finalizado' },
    { id: '0984', date: '2026-05-28', client: 'Ana Gómez', vehicle: 'Honda Civic 2020', mechanic: 'Miguel Torres', status: 'Finalizado' },
    { id: '0971', date: '2026-05-25', client: 'Luis Torres', vehicle: 'Ford Explorer 2019', mechanic: 'Juan Silva', status: 'Cancelado' }
  ];
}
