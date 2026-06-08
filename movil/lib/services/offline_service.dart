import 'package:sqflite/sqflite.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;

class OfflineService {
  static const _dbName = 'emergencias_offline.db';
  static const _table = 'pending_emergencies';

  Database? _db;

  Future<Database> get database async {
    _db ??= await _initDb();
    return _db!;
  }

  Future<Database> _initDb() async {
    final dir = await getApplicationDocumentsDirectory();
    final path = p.join(dir.path, _dbName);

    return openDatabase(
      path,
      version: 2,
      onUpgrade: (db, oldVersion, newVersion) async {
        if (oldVersion < 2) {
          await db.execute('ALTER TABLE $_table ADD COLUMN audio_base64 TEXT');
        }
      },
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE $_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT,
            vehiculo_id INTEGER,
            descripcion TEXT,
            latitud REAL,
            longitud REAL,
            imagen_base64 TEXT,
            audio_base64 TEXT,
            created_at TEXT,
            synced INTEGER DEFAULT 0
          )
        ''');
      },
    );
  }

  Future<int> saveEmergency(Map<String, dynamic> data) async {
    final db = await database;
    return db.insert(_table, data);
  }

  Future<List<Map<String, dynamic>>> getPendingEmergencies() async {
    final db = await database;
    return db.query(_table, where: 'synced = ?', whereArgs: [0]);
  }

  Future<int> markAsSynced(int id) async {
    final db = await database;
    return db.update(
      _table,
      {'synced': 1},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<int> deleteSynced() async {
    final db = await database;
    return db.delete(_table, where: 'synced = ?', whereArgs: [1]);
  }
}
