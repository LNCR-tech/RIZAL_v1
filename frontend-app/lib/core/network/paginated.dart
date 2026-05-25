/// Unified paginated result. Unwraps either the backend envelope
/// `{data, page, total, total_pages, limit, next, prev}` or a bare JSON list,
/// matching `extractPagedData` in the web client.
class Paginated<T> {
  const Paginated({
    required this.data,
    this.page = 1,
    this.total = 0,
    this.totalPages = 0,
    this.limit = 0,
    this.next,
    this.prev,
  });

  final List<T> data;
  final int page;
  final int total;
  final int totalPages;
  final int limit;
  final String? next;
  final String? prev;

  bool get isEmpty => data.isEmpty;
  bool get isNotEmpty => data.isNotEmpty;
  bool get hasNext => next != null && next!.isNotEmpty;

  static Paginated<T> from<T>(dynamic payload, T Function(dynamic) item) {
    if (payload is List) {
      final d = payload.map(item).toList();
      return Paginated<T>(
        data: d,
        page: 1,
        total: d.length,
        totalPages: 1,
        limit: d.length,
      );
    }
    if (payload is Map && payload['data'] is List) {
      final d = (payload['data'] as List).map(item).toList();
      int asInt(dynamic v) => (v is num) ? v.toInt() : 0;
      return Paginated<T>(
        data: d,
        page: asInt(payload['page']) == 0 ? 1 : asInt(payload['page']),
        total: asInt(payload['total']),
        totalPages: asInt(payload['total_pages']),
        limit: asInt(payload['limit']),
        next: payload['next']?.toString(),
        prev: payload['prev']?.toString(),
      );
    }
    return Paginated<T>(data: const []);
  }
}
