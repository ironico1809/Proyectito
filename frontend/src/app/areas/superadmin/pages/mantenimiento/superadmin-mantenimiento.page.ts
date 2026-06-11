// ============================================================
// superadmin-mantenimiento.page.ts
// CU-BACKUP: Mantenimiento Técnico y Respaldos
// ============================================================
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BackupApi, BackupItem, ConfigBackup } from '../../../../infra/api/backup.api';

@Component({
  selector: 'ev-superadmin-mantenimiento',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './superadmin-mantenimiento.page.html',
  styleUrl: './superadmin-mantenimiento.page.css',
})
export class SuperadminMantenimientoPage implements OnInit {
  backups: BackupItem[] = [];
  config: ConfigBackup = { hora_automatico: null, automatico_activo: false };

  generando = false;
  guardando = false;
  mensaje: string | null = null;
  mensajeTipo: 'success' | 'error' = 'success';

  constructor(private backupApi: BackupApi) {}

  ngOnInit(): void {
    this.cargarHistorial();
    this.cargarConfig();
  }

  cargarHistorial(): void {
    this.backupApi.historial().subscribe({
      next: (data) => (this.backups = data),
      error: (err) => console.error('Error cargando historial:', err),
    });
  }

  cargarConfig(): void {
    this.backupApi.obtenerConfig().subscribe({
      next: (data) => (this.config = data),
      error: (err) => console.error('Error cargando config:', err),
    });
  }

  guardarHorario(): void {
    this.guardando = true;
    this.backupApi.guardarConfig(this.config).subscribe({
      next: (data) => {
        this.config = data;
        this.guardando = false;
        this.mostrarMensaje('Configuración guardada correctamente', 'success');
      },
      error: () => {
        this.guardando = false;
        this.mostrarMensaje('Error al guardar configuración', 'error');
      },
    });
  }

  generarManual(): void {
    this.generando = true;
    this.backupApi.generarManual().subscribe({
      next: () => {
        this.generando = false;
        this.cargarHistorial();
        this.mostrarMensaje('Copia de seguridad generada exitosamente', 'success');
      },
      error: () => {
        this.generando = false;
        this.mostrarMensaje('Error al generar copia de seguridad', 'error');
      },
    });
  }

  descargar(backup: BackupItem): void {
    const url = this.backupApi.descargarUrl(backup.id);
    window.open(url, '_blank');
  }

  eliminar(id: number): void {
    if (!confirm('¿Estás seguro de eliminar esta copia de seguridad?')) return;
    this.backupApi.eliminar(id).subscribe({
      next: () => {
        this.cargarHistorial();
        this.mostrarMensaje('Backup eliminado correctamente', 'success');
      },
      error: () => this.mostrarMensaje('Error al eliminar backup', 'error'),
    });
  }

  formatBytes(bytes: number | null): string {
    if (!bytes || bytes === 0) return '—';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  formatFecha(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleDateString('es-ES', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  }

  private mostrarMensaje(texto: string, tipo: 'success' | 'error'): void {
    this.mensaje = texto;
    this.mensajeTipo = tipo;
    setTimeout(() => (this.mensaje = null), 4000);
  }
}