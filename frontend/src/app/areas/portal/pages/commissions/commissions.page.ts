import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'ev-commissions-page',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './commissions.page.html',
  styleUrl: './commissions.page.css',
})
export class CommissionsPage {
  totalCommissions = 1450.00;
  totalGross = 14500.00;
  
  breakdown = [
    { workshop: 'AutoService Center', services: 45, gross: 4500.00, comission: 450.00 },
    { workshop: 'Mecánica Rápida SRL', services: 38, gross: 3800.00, comission: 380.00 },
    { workshop: 'Taller Los Andes', services: 32, gross: 3200.00, comission: 320.00 },
    { workshop: 'Garage Central', services: 27, gross: 3000.00, comission: 300.00 }
  ];
}
