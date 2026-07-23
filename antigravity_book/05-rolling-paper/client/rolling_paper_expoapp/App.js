import React, { useState, useRef, useEffect } from "react";
import {
  BackHandler,
  Platform,
  ActivityIndicator,
  View,
  StyleSheet,
} from "react-native";
import { WebView } from "react-native-webview";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";

export default function App() {
  const webViewRef = useRef(null);
  const [canGoBack, setCanGoBack] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // 안드로이드 뒤로 가기 버튼 처리
  useEffect(() => {
    const backAction = () => {
      if (canGoBack && webViewRef.current) {
        webViewRef.current.goBack();
        return true; // 앱 종료 방지 및 이전 페이지로 이동
      }
      return false; // 더 이상 뒤로 갈 페이지가 없으면 앱 종료 (기본 동작 수행)
    };

    const backHandler = BackHandler.addEventListener(
      "hardwareBackPress",
      backAction,
    );

    return () => backHandler.remove();
  }, [canGoBack]);

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.container}>
        {/* 상태바 스타일 설정 (선택 사항: 'auto', 'dark', 'light') */}
        <StatusBar style="auto" />

        <WebView
          ref={webViewRef}
          source={{ uri: "https://rolling-paper-chi.vercel.app/#" }}
          style={styles.webview}
          onNavigationStateChange={(navState) => {
            setCanGoBack(navState.canGoBack);
          }}
          onLoadStart={() => setIsLoading(true)}
          onLoadEnd={() => setIsLoading(false)}
          // 안드로이드에서 텍스트 크기 등 설정이 필요한 경우 추가 가능
          javaScriptEnabled={true}
          domStorageEnabled={true}
        />

        {/* 로딩 스피너 표시 */}
        {isLoading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#0000ff" />
          </View>
        )}
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#fff", // 배경색 (필요시 변경)
  },
  webview: {
    flex: 1,
  },
  loadingContainer: {
    position: "absolute", // WebView 위에 겹쳐서 표시
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "rgba(255, 255, 255, 0.5)", // 반투명 배경 (선택 사항)
  },
});
