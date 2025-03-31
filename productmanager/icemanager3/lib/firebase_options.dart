import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart' show defaultTargetPlatform, TargetPlatform;

class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    return android;
  }

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'AIzaSyDO-2ZNacHxIW1Jluxz7jdgvsEY3iAMBRo',
    appId: '1:958984931859:android:3efe547a1791a6259b0de6',
    messagingSenderId: '958984931859',
    projectId: 'icemanager3',
    storageBucket: 'icemanager3.appspot.com',
  );
}
