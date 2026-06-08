import 'package:dio/dio.dart';

import '../config/api_config.dart';
import 'storage_service.dart';

class ApiService {
  late final Dio _dio;
  final StorageService _storage;
  void Function()? onUnauthorized;

  ApiService(this._storage) {
    _dio = Dio(BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: ApiConfig.timeout,
      receiveTimeout: ApiConfig.timeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        print("API_REQ: [${options.method}] ${options.baseUrl}${options.path}");
        print("API_REQ_HEADERS: ${options.headers}");
        final token = _storage.getToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onResponse: (response, handler) {
        print("API_RES: [${response.statusCode}] ${response.requestOptions.method} ${response.requestOptions.path}");
        handler.next(response);
      },
      onError: (error, handler) async {
        print("API_ERR: [${error.response?.statusCode}] ${error.requestOptions.method} ${error.requestOptions.path}");
        print("API_ERR_MSG: ${error.message}");
        print("API_ERR_DETAIL: ${error.error}");
        if (error.response?.statusCode == 401) {
          final isLogout = error.requestOptions.path.contains('/auth/logout');
          if (!isLogout) {
            await _storage.clear();
            if (onUnauthorized != null) {
              onUnauthorized!();
            }
          }
        }
        handler.next(error);
      },
    ));
  }

  Future<Response> get(
    String path, {
    Map<String, dynamic>? queryParameters,
  }) =>
      _dio.get(path, queryParameters: queryParameters);

  Future<Response> post(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
  }) =>
      _dio.post(path, data: data, queryParameters: queryParameters);

  Future<Response> put(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
  }) =>
      _dio.put(path, data: data, queryParameters: queryParameters);

  Future<Response> patch(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
  }) =>
      _dio.patch(path, data: data, queryParameters: queryParameters);

  Future<Response> delete(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
  }) =>
      _dio.delete(path, data: data, queryParameters: queryParameters);
}
