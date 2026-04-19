import { Component, OnInit, inject } from '@angular/core'; // ✅ CORRECTO
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-historial-tecnico',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './historial-tecnico.html',
  styleUrls: ['./historial-tecnico.css']
})
export class HistorialTecnico implements OnInit {
  private http = inject(HttpClient);
  
  historial: any[] = [];
  cargando = true;
  idTecnico: number = 0;

  ngOnInit(): void {
    // Obtenemos el ID del técnico desde el login
    this.idTecnico = Number(localStorage.getItem('id_entidad')) || 0;
    this.cargarHistorial();
  }

  cargarHistorial(): void {
    this.http.get<any[]>(`http://localhost:8000/incidentes/historial/tecnico/${this.idTecnico}`).subscribe({
      next: (data) => {
        this.historial = data;
        this.cargando = false;
      },
      error: (err) => {
        console.error('Error al cargar historial:', err);
        this.cargando = false;
      }
    });
  }
}