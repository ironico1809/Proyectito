import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'ev-income-page',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './income.page.html',
  styleUrl: './income.page.css',
})
export class IncomePage {
  totalGross = 14500.00;
  totalCommissions = 1450.00;
  totalNet = this.totalGross - this.totalCommissions;
  
  payments = [
    { period: 'Junio 2026', gross: 4500.00, comission: 450.00, net: 4050.00, status: 'Pagado' },
    { period: 'Mayo 2026', gross: 5000.00, comission: 500.00, net: 4500.00, status: 'Pagado' },
    { period: 'Abril 2026', gross: 5000.00, comission: 500.00, net: 4500.00, status: 'Pagado' }
  ];
}
