import 'package:flutter/material.dart';

import 'screens/family_recognition_screen.dart';

void main() {
  runApp(const RemembranceApp());
}

class RemembranceApp extends StatelessWidget {
  const RemembranceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Remembrance',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF2E7D7A),
        ),
        useMaterial3: true,
      ),
      home: const FamilyRecognitionHomePage(),
    );
  }
}

class FamilyRecognitionHomePage extends StatelessWidget {
  const FamilyRecognitionHomePage({super.key});

  void _openRecognition(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => const FamilyRecognitionScreen(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Remembrance')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.favorite,
                color: Color(0xFF2E7D7A),
                size: 64,
              ),
              const SizedBox(height: 20),
              Text(
                'Family recognition',
                style: Theme.of(context).textTheme.headlineSmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),
              Text(
                'Open the camera preview to continue.',
                style: Theme.of(context).textTheme.bodyLarge,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 28),
              FilledButton.icon(
                onPressed: () => _openRecognition(context),
                icon: const Icon(Icons.camera_alt),
                label: const Text('OPEN FAMILY RECOGNITION'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
