
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

enum FamilyRecognitionStatus {
  searching,
  recognised,
  uncertain,
  unknown,
  error,
}

class FamilyRecognitionScreen extends StatefulWidget {
  const FamilyRecognitionScreen({
    super.key,
    this.onHelpRequested,
  });

  final VoidCallback? onHelpRequested;

  @override
  State<FamilyRecognitionScreen> createState() =>
      _FamilyRecognitionScreenState();
}

class _FamilyRecognitionScreenState
    extends State<FamilyRecognitionScreen> {
  CameraController? _cameraController;

  FamilyRecognitionStatus _status =
      FamilyRecognitionStatus.searching;

  String _name = '';
  String _relationship = '';
  String _greeting = '';
  String? _cameraError;
  bool _showHelp = false;

  @override
  void initState() {
    super.initState();
    _initialiseCamera();
  }

  Future<void> _initialiseCamera() async {
    try {
      final cameras = await availableCameras();

      if (cameras.isEmpty) {
        throw Exception('No camera was found on this device.');
      }

      // Prefer the front camera for a face-to-face experience.
      final camera = cameras.firstWhere(
        (item) => item.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );

      final controller = CameraController(
        camera,
        ResolutionPreset.medium,
        enableAudio: false,
      );

      await controller.initialize();

      if (!mounted) {
        await controller.dispose();
        return;
      }

      setState(() {
        _cameraController = controller;
        _cameraError = null;
      });
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _cameraError =
            'The camera could not be opened. Please ask your caregiver for help.';
        _status = FamilyRecognitionStatus.error;
      });

      debugPrint('Camera initialisation failed: $error');
    }
  }

  // The future recognition engine should call this method only
  // after it has produced a sufficiently reliable result.
  void updateRecognition({
    required FamilyRecognitionStatus status,
    String name = '',
    String relationship = '',
    String greeting = '',
  }) {
    if (!mounted) return;

    setState(() {
      _status = status;
      _name = name;
      _relationship = relationship;
      _greeting = greeting;
      _showHelp = false;
    });
  }

  void _showCaregiverHelp() {
    setState(() {
      _showHelp = true;
    });

    widget.onHelpRequested?.call();
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final controller = _cameraController;

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand,
        children: [
          // Live camera preview.
          if (controller != null &&
              controller.value.isInitialized)
            Center(
              child: AspectRatio(
                aspectRatio: controller.value.aspectRatio,
                child: CameraPreview(controller),
              ),
            )
          else
            const ColoredBox(
              color: Color(0xFF202725),
              child: Center(
                child: CircularProgressIndicator(
                  color: Color(0xFF32FFF7),
                ),
              ),
            ),

          // Dark overlay improves text contrast over the camera.
          const DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Color(0x66000000),
                  Colors.transparent,
                  Color(0x77000000),
                ],
              ),
            ),
          ),

          SafeArea(
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.favorite,
                        color: Color(0xFF32FFF7),
                        size: 30,
                      ),
                      const SizedBox(width: 10),
                      const Expanded(
                        child: Text(
                          'REMEMBRANCE',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1.2,
                          ),
                        ),
                      ),
                      IconButton(
                        tooltip: 'Close camera',
                        onPressed: () => Navigator.of(context).pop(),
                        icon: const Icon(
                          Icons.close,
                          color: Colors.white,
                          size: 30,
                        ),
                      ),
                    ],
                  ),
                ),

                const Spacer(),

                // Recognition popup.
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: _buildRecognitionPanel(),
                ),

                const Spacer(),

                // Large caregiver-help button.
                Padding(
                  padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
                  child: SizedBox(
                    width: double.infinity,
                    height: 66,
                    child: ElevatedButton.icon(
                      onPressed: _showCaregiverHelp,
                      icon: const Icon(
                        Icons.support_agent,
                        size: 30,
                      ),
                      label: const Text(
                        'I NEED HELP',
                        style: TextStyle(
                          fontSize: 21,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF2E7D7A),
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(18),
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),

          if (_cameraError != null)
            Container(
              color: Colors.black87,
              padding: const EdgeInsets.all(28),
              child: Center(
                child: Text(
                  _cameraError!,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    height: 1.5,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildRecognitionPanel() {
    final bool recognised =
        _status == FamilyRecognitionStatus.recognised;
    final bool searching =
        _status == FamilyRecognitionStatus.searching;
    final bool uncertain =
        _status == FamilyRecognitionStatus.uncertain;
    final bool unknown =
        _status == FamilyRecognitionStatus.unknown;

    String title;
    String subtitle;
    String greeting;
    IconData icon;
    Color panelColor;

    if (_showHelp) {
      title = 'You are not alone.';
      subtitle = 'Please ask your caregiver to help you.';
      greeting = '';
      icon = Icons.support_agent;
      panelColor = const Color(0xFF2E7D7A);
    } else if (recognised) {
      title = 'This looks like $_name';
      subtitle = _relationship.isEmpty
          ? 'Your family member'
          : 'Your $_relationship';
      greeting = _greeting;
      icon = Icons.favorite;
      panelColor = const Color(0xFF2E7D7A);
    } else if (uncertain) {
      title = 'I am not sure who this is.';
      subtitle = 'Please look at the camera again.';
      greeting = 'You can ask your caregiver for help.';
      icon = Icons.help_outline;
      panelColor = const Color(0xFF55534A);
    } else if (unknown) {
      title = 'I do not recognise this person.';
      subtitle = 'Your family member may not be registered.';
      greeting = 'Please ask your caregiver for help.';
      icon = Icons.info_outline;
      panelColor = const Color(0xFF55534A);
    } else if (_status == FamilyRecognitionStatus.error) {
      title = 'Camera unavailable';
      subtitle = 'Please ask your caregiver for help.';
      greeting = '';
      icon = Icons.videocam_off;
      panelColor = const Color(0xFF55534A);
    } else {
      title = 'Looking for your family member...';
      subtitle = 'Please look towards the camera.';
      greeting = 'Your family information will appear here.';
      icon = Icons.face;
      panelColor = const Color(0xFF2E7D7A);
    }

    return Semantics(
      liveRegion: true,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.fromLTRB(22, 26, 22, 26),
        decoration: BoxDecoration(
          color: panelColor.withValues(alpha: 0.94),
          borderRadius: BorderRadius.circular(26),
          border: Border.all(
            color: Colors.white.withValues(alpha: 0.25),
            width: 1.5,
          ),
          boxShadow: const [
            BoxShadow(
              color: Colors.black26,
              blurRadius: 18,
              offset: Offset(0, 6),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: Colors.white, size: 38),
            const SizedBox(height: 14),
            Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 27,
                height: 1.25,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              subtitle,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 21,
                height: 1.35,
                fontWeight: FontWeight.w600,
              ),
            ),
            if (greeting.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                greeting,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  height: 1.4,
                ),
              ),
            ],
            if (searching && !_showHelp) ...[
              const SizedBox(height: 18),
              const LinearProgressIndicator(
                color: Color(0xFF32FFF7),
                backgroundColor: Colors.white24,
              ),
            ],
          ],
        ),
      ),
    );
  }
}
