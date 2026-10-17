import 'package:flutter_test/flutter_test.dart';

import 'package:remembrance_face_unlock/main.dart';

void main() {
  testWidgets('home screen opens family recognition', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const RemembranceApp());

    expect(find.text('Family recognition'), findsOneWidget);
    expect(find.text('OPEN FAMILY RECOGNITION'), findsOneWidget);

    await tester.tap(find.text('OPEN FAMILY RECOGNITION'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));

    expect(find.text('I NEED HELP'), findsOneWidget);
    expect(find.byTooltip('Close camera'), findsOneWidget);
  });
}
