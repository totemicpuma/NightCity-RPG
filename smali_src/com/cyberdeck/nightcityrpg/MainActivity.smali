.class public Lcom/cyberdeck/nightcityrpg/MainActivity;
.super Landroid/app/Activity;

.field private webView:Landroid/webkit/WebView;

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Landroid/app/Activity;-><init>()V
    return-void
.end method

.method protected onCreate(Landroid/os/Bundle;)V
    .registers 7
    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V

    const/4 v0, 0x1
    invoke-virtual {p0, v0}, Landroid/app/Activity;->requestWindowFeature(I)Z

    # Solicita permissão POST_NOTIFICATIONS no Android 13+ (SDK >= 33)
    sget v1, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v2, 0x21
    if-lt v1, v2, :cond_perm_done
    new-array v2, v0, [Ljava/lang/String;
    const/4 v3, 0x0
    const-string v4, "android.permission.POST_NOTIFICATIONS"
    aput-object v4, v2, v3
    const/16 v3, 0x65
    invoke-virtual {p0, v2, v3}, Landroid/app/Activity;->requestPermissions([Ljava/lang/String;I)V
    :cond_perm_done

    new-instance v1, Landroid/webkit/WebView;
    invoke-direct {v1, p0}, Landroid/webkit/WebView;-><init>(Landroid/content/Context;)V
    iput-object v1, p0, Lcom/cyberdeck/nightcityrpg/MainActivity;->webView:Landroid/webkit/WebView;

    const v2, -0xf9f8f5
    invoke-virtual {v1, v2}, Landroid/webkit/WebView;->setBackgroundColor(I)V

    invoke-virtual {v1}, Landroid/webkit/WebView;->getSettings()Landroid/webkit/WebSettings;
    move-result-object v2

    invoke-virtual {v2, v0}, Landroid/webkit/WebSettings;->setJavaScriptEnabled(Z)V
    invoke-virtual {v2, v0}, Landroid/webkit/WebSettings;->setDomStorageEnabled(Z)V
    invoke-virtual {v2, v0}, Landroid/webkit/WebSettings;->setDatabaseEnabled(Z)V
    invoke-virtual {v2, v0}, Landroid/webkit/WebSettings;->setAllowFileAccess(Z)V
    invoke-virtual {v2, v0}, Landroid/webkit/WebSettings;->setAllowContentAccess(Z)V
    invoke-virtual {v2, v0}, Landroid/webkit/WebSettings;->setAllowFileAccessFromFileURLs(Z)V
    invoke-virtual {v2, v0}, Landroid/webkit/WebSettings;->setAllowUniversalAccessFromFileURLs(Z)V

    new-instance v3, Landroid/webkit/WebChromeClient;
    invoke-direct {v3}, Landroid/webkit/WebChromeClient;-><init>()V
    invoke-virtual {v1, v3}, Landroid/webkit/WebView;->setWebChromeClient(Landroid/webkit/WebChromeClient;)V

    new-instance v3, Landroid/webkit/WebViewClient;
    invoke-direct {v3}, Landroid/webkit/WebViewClient;-><init>()V
    invoke-virtual {v1, v3}, Landroid/webkit/WebView;->setWebViewClient(Landroid/webkit/WebViewClient;)V

    new-instance v3, Lcom/cyberdeck/nightcityrpg/AndroidBridge;
    invoke-direct {v3, p0}, Lcom/cyberdeck/nightcityrpg/AndroidBridge;-><init>(Landroid/content/Context;)V
    const-string v4, "AndroidBridge"
    invoke-virtual {v1, v3, v4}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V

    invoke-virtual {p0, v1}, Landroid/app/Activity;->setContentView(Landroid/view/View;)V

    const-string v3, "file:///android_asset/index.html"
    invoke-virtual {v1, v3}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V

    return-void
.end method

.method protected onResume()V
    .registers 3
    invoke-super {p0}, Landroid/app/Activity;->onResume()V
    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/MainActivity;->webView:Landroid/webkit/WebView;
    if-eqz v0, :cond_done
    const-string v1, "javascript:if(window.consumeNativeNotificationActions)window.consumeNativeNotificationActions();if(window.syncAndroidSystemNotifications)window.syncAndroidSystemNotifications();"
    invoke-virtual {v0, v1}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V
    :cond_done
    return-void
.end method

.method public onRequestPermissionsResult(I[Ljava/lang/String;[I)V
    .registers 6
    invoke-super {p0, p1, p2, p3}, Landroid/app/Activity;->onRequestPermissionsResult(I[Ljava/lang/String;[I)V
    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/MainActivity;->webView:Landroid/webkit/WebView;
    if-eqz v0, :cond_done
    const-string v1, "javascript:if(window.syncAndroidSystemNotifications)window.syncAndroidSystemNotifications();"
    invoke-virtual {v0, v1}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V
    :cond_done
    return-void
.end method

.method public onBackPressed()V
    .registers 3
    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/MainActivity;->webView:Landroid/webkit/WebView;
    if-eqz v0, :cond_super
    invoke-virtual {v0}, Landroid/webkit/WebView;->canGoBack()Z
    move-result v1
    if-eqz v1, :cond_super
    invoke-virtual {v0}, Landroid/webkit/WebView;->goBack()V
    return-void
    :cond_super
    invoke-super {p0}, Landroid/app/Activity;->onBackPressed()V
    return-void
.end method
