.class public Lcom/cyberdeck/nightcityrpg/AndroidBridge;
.super Ljava/lang/Object;

.field private context:Landroid/content/Context;

.method public constructor <init>(Landroid/content/Context;)V
    .registers 2
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/cyberdeck/nightcityrpg/AndroidBridge;->context:Landroid/content/Context;
    return-void
.end method

.method public areNotificationsEnabled()Z
    .registers 4
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/AndroidBridge;->context:Landroid/content/Context;
    const-string v1, "notification"
    invoke-virtual {v0, v1}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;
    move-result-object v1
    check-cast v1, Landroid/app/NotificationManager;

    sget v2, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v0, 0x18
    if-lt v2, v0, :cond_true
    invoke-virtual {v1}, Landroid/app/NotificationManager;->areNotificationsEnabled()Z
    move-result v0
    return v0

    :cond_true
    const/4 v0, 0x1
    return v0
.end method

.method public openNotificationSettings()V
    .registers 5
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/AndroidBridge;->context:Landroid/content/Context;
    new-instance v1, Landroid/content/Intent;
    const-string v2, "android.settings.APP_NOTIFICATION_SETTINGS"
    invoke-direct {v1, v2}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V
    const-string v2, "android.provider.extra.APP_PACKAGE"
    const-string v3, "com.cyberdeck.nightcityrpg"
    invoke-virtual {v1, v2, v3}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;
    const/high16 v2, 0x10000000
    invoke-virtual {v1, v2}, Landroid/content/Intent;->addFlags(I)Landroid/content/Intent;
    invoke-virtual {v0, v1}, Landroid/content/Context;->startActivity(Landroid/content/Intent;)V

    const-string v1, "\ud83d\udcf2 Ative a chave \'Permitir notifica\u00e7\u00f5es\' nesta tela do Samsung!"
    const/4 v2, 0x1
    invoke-static {v0, v1, v2}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v1
    invoke-virtual {v1}, Landroid/widget/Toast;->show()V
    return-void
.end method

.method public showQuestNotification(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;I)V
    .registers 15
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/AndroidBridge;->context:Landroid/content/Context;
    const-string v1, "notification"
    invoke-virtual {v0, v1}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;
    move-result-object v1
    check-cast v1, Landroid/app/NotificationManager;

    const-string v2, "nc_daily_channel_v3"
    sget v3, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v4, 0x1a
    if-lt v3, v4, :cond_legacy

    new-instance v4, Landroid/app/NotificationChannel;
    const-string v5, "Daily Quests // Night City RPG"
    const/4 v6, 0x4
    invoke-direct {v4, v2, v5, v6}, Landroid/app/NotificationChannel;-><init>(Ljava/lang/String;Ljava/lang/CharSequence;I)V
    invoke-virtual {v1, v4}, Landroid/app/NotificationManager;->createNotificationChannel(Landroid/app/NotificationChannel;)V

    new-instance v4, Landroid/app/Notification$Builder;
    invoke-direct {v4, v0, v2}, Landroid/app/Notification$Builder;-><init>(Landroid/content/Context;Ljava/lang/String;)V
    goto :goto_build

    :cond_legacy
    new-instance v4, Landroid/app/Notification$Builder;
    invoke-direct {v4, v0}, Landroid/app/Notification$Builder;-><init>(Landroid/content/Context;)V

    :goto_build
    const/high16 v5, 0x7f010000
    invoke-virtual {v4, v5}, Landroid/app/Notification$Builder;->setSmallIcon(I)Landroid/app/Notification$Builder;

    # Carrega o ícone Cyberpunk colorido também como LargeIcon na notificação Samsung One UI
    invoke-virtual {v0}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;
    move-result-object v6
    invoke-static {v6, v5}, Landroid/graphics/BitmapFactory;->decodeResource(Landroid/content/res/Resources;I)Landroid/graphics/Bitmap;
    move-result-object v6
    if-eqz v6, :cond_no_large
    invoke-virtual {v4, v6}, Landroid/app/Notification$Builder;->setLargeIcon(Landroid/graphics/Bitmap;)Landroid/app/Notification$Builder;
    :cond_no_large
    invoke-virtual {v4, p2}, Landroid/app/Notification$Builder;->setContentTitle(Ljava/lang/CharSequence;)Landroid/app/Notification$Builder;
    invoke-virtual {v4, p3}, Landroid/app/Notification$Builder;->setContentText(Ljava/lang/CharSequence;)Landroid/app/Notification$Builder;
    const/4 v5, 0x1
    invoke-virtual {v4, v5}, Landroid/app/Notification$Builder;->setAutoCancel(Z)Landroid/app/Notification$Builder;

    # Estilo expansível BigTextStyle para ler toda a Daily Quest na barra de notificações
    new-instance v5, Landroid/app/Notification$BigTextStyle;
    invoke-direct {v5}, Landroid/app/Notification$BigTextStyle;-><init>()V
    invoke-virtual {v5, p3}, Landroid/app/Notification$BigTextStyle;->bigText(Ljava/lang/CharSequence;)Landroid/app/Notification$BigTextStyle;
    invoke-virtual {v4, v5}, Landroid/app/Notification$Builder;->setStyle(Landroid/app/Notification$Style;)Landroid/app/Notification$Builder;

    # Define flags do PendingIntent (FLAG_UPDATE_CURRENT | FLAG_IMMUTABLE no SDK >= 23)
    const/high16 v5, 0x08000000
    const/16 v6, 0x17
    if-lt v3, v6, :cond_flags_ok
    const/high16 v5, 0x0c000000
    :cond_flags_ok

    # Botão 1 na Notificação do Android: [✔ Concluir (+10 XP)]
    new-instance v6, Landroid/content/Intent;
    const-class v7, Lcom/cyberdeck/nightcityrpg/NotificationActionReceiver;
    invoke-direct {v6, v0, v7}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    const-string v8, "com.cyberdeck.nightcityrpg.ACTION_COMPLETE"
    invoke-virtual {v6, v8}, Landroid/content/Intent;->setAction(Ljava/lang/String;)Landroid/content/Intent;
    const-string v8, "nc_action"
    const-string v9, "complete"
    invoke-virtual {v6, v8, v9}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;
    const-string v8, "nc_quest_id"
    invoke-virtual {v6, v8, p1}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;
    const-string v8, "nc_notif_id"
    invoke-virtual {v6, v8, p4}, Landroid/content/Intent;->putExtra(Ljava/lang/String;I)Landroid/content/Intent;

    mul-int/lit8 v8, p4, 0x2
    invoke-static {v0, v8, v6, v5}, Landroid/app/PendingIntent;->getBroadcast(Landroid/content/Context;ILandroid/content/Intent;I)Landroid/app/PendingIntent;
    move-result-object v8
    const/4 v9, 0x0
    const-string v6, "\u2714 Concluir (+10 XP)"
    invoke-virtual {v4, v9, v6, v8}, Landroid/app/Notification$Builder;->addAction(ILjava/lang/CharSequence;Landroid/app/PendingIntent;)Landroid/app/Notification$Builder;

    # Botão 2 na Notificação do Android: [🔕 Silenciar]
    new-instance v6, Landroid/content/Intent;
    invoke-direct {v6, v0, v7}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    const-string v8, "com.cyberdeck.nightcityrpg.ACTION_MUTE"
    invoke-virtual {v6, v8}, Landroid/content/Intent;->setAction(Ljava/lang/String;)Landroid/content/Intent;
    const-string v8, "nc_action"
    const-string v9, "mute"
    invoke-virtual {v6, v8, v9}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;
    const-string v8, "nc_quest_id"
    invoke-virtual {v6, v8, p1}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;
    const-string v8, "nc_notif_id"
    invoke-virtual {v6, v8, p4}, Landroid/content/Intent;->putExtra(Ljava/lang/String;I)Landroid/content/Intent;

    mul-int/lit8 v8, p4, 0x2
    add-int/lit8 v8, v8, 0x1
    invoke-static {v0, v8, v6, v5}, Landroid/app/PendingIntent;->getBroadcast(Landroid/content/Context;ILandroid/content/Intent;I)Landroid/app/PendingIntent;
    move-result-object v8
    const/4 v9, 0x0
    const-string v6, "\ud83d\udd15 Silenciar"
    invoke-virtual {v4, v9, v6, v8}, Landroid/app/Notification$Builder;->addAction(ILjava/lang/CharSequence;Landroid/app/PendingIntent;)Landroid/app/Notification$Builder;

    # Toque no corpo da notificação abre o app
    new-instance v6, Landroid/content/Intent;
    const-class v7, Lcom/cyberdeck/nightcityrpg/MainActivity;
    invoke-direct {v6, v0, v7}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    const/high16 v7, 0x24000000
    invoke-virtual {v6, v7}, Landroid/content/Intent;->setFlags(I)Landroid/content/Intent;
    invoke-static {v0, p4, v6, v5}, Landroid/app/PendingIntent;->getActivity(Landroid/content/Context;ILandroid/content/Intent;I)Landroid/app/PendingIntent;
    move-result-object v6
    invoke-virtual {v4, v6}, Landroid/app/Notification$Builder;->setContentIntent(Landroid/app/PendingIntent;)Landroid/app/Notification$Builder;

    invoke-virtual {v4}, Landroid/app/Notification$Builder;->build()Landroid/app/Notification;
    move-result-object v5
    invoke-virtual {v1, p4, v5}, Landroid/app/NotificationManager;->notify(ILandroid/app/Notification;)V

    return-void
.end method

.method public cancelNotification(I)V
    .registers 4
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/AndroidBridge;->context:Landroid/content/Context;
    const-string v1, "notification"
    invoke-virtual {v0, v1}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;
    move-result-object v1
    check-cast v1, Landroid/app/NotificationManager;
    invoke-virtual {v1, p1}, Landroid/app/NotificationManager;->cancel(I)V
    return-void
.end method

.method public cancelAllNotifications()V
    .registers 3
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/AndroidBridge;->context:Landroid/content/Context;
    const-string v1, "notification"
    invoke-virtual {v0, v1}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;
    move-result-object v1
    check-cast v1, Landroid/app/NotificationManager;
    invoke-virtual {v1}, Landroid/app/NotificationManager;->cancelAll()V
    return-void
.end method

.method public httpRequest(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    .registers 12
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    :try_start_http
    new-instance v0, Ljava/net/URL;
    invoke-direct {v0, p1}, Ljava/net/URL;-><init>(Ljava/lang/String;)V
    invoke-virtual {v0}, Ljava/net/URL;->openConnection()Ljava/net/URLConnection;
    move-result-object v0
    check-cast v0, Ljava/net/HttpURLConnection;

    invoke-virtual {v0, p2}, Ljava/net/HttpURLConnection;->setRequestMethod(Ljava/lang/String;)V
    const/16 v1, 0x3a98
    invoke-virtual {v0, v1}, Ljava/net/HttpURLConnection;->setConnectTimeout(I)V
    const/16 v1, 0x4e20
    invoke-virtual {v0, v1}, Ljava/net/HttpURLConnection;->setReadTimeout(I)V

    const-string v1, "Accept"
    const-string v2, "application/json, text/calendar, */*"
    invoke-virtual {v0, v1, v2}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V
    const-string v1, "User-Agent"
    const-string v2, "Mozilla/5.0 NightCityRPG-Android/2.0"
    invoke-virtual {v0, v1, v2}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V

    if-eqz p3, :cond_no_auth
    invoke-virtual {p3}, Ljava/lang/String;->length()I
    move-result v1
    if-lez v1, :cond_no_auth
    const-string v1, "Authorization"
    invoke-virtual {v0, v1, p3}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V
    :cond_no_auth

    if-eqz p4, :cond_no_body
    invoke-virtual {p4}, Ljava/lang/String;->length()I
    move-result v1
    if-lez v1, :cond_no_body
    const-string v1, "Content-Type"
    const-string v2, "application/json; charset=UTF-8"
    invoke-virtual {v0, v1, v2}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V
    const/4 v1, 0x1
    invoke-virtual {v0, v1}, Ljava/net/HttpURLConnection;->setDoOutput(Z)V
    invoke-virtual {v0}, Ljava/net/HttpURLConnection;->getOutputStream()Ljava/io/OutputStream;
    move-result-object v1
    const-string v2, "UTF-8"
    invoke-virtual {p4, v2}, Ljava/lang/String;->getBytes(Ljava/lang/String;)[B
    move-result-object v2
    invoke-virtual {v1, v2}, Ljava/io/OutputStream;->write([B)V
    invoke-virtual {v1}, Ljava/io/OutputStream;->close()V
    :cond_no_body

    invoke-virtual {v0}, Ljava/net/HttpURLConnection;->getResponseCode()I
    move-result v1
    const/16 v2, 0x190
    if-ge v1, v2, :cond_err_stream
    invoke-virtual {v0}, Ljava/net/HttpURLConnection;->getInputStream()Ljava/io/InputStream;
    move-result-object v1
    goto :cond_got_stream

    :cond_err_stream
    invoke-virtual {v0}, Ljava/net/HttpURLConnection;->getErrorStream()Ljava/io/InputStream;
    move-result-object v1

    :cond_got_stream
    if-eqz v1, :cond_empty
    new-instance v2, Ljava/io/InputStreamReader;
    const-string v3, "UTF-8"
    invoke-direct {v2, v1, v3}, Ljava/io/InputStreamReader;-><init>(Ljava/io/InputStream;Ljava/lang/String;)V
    new-instance v3, Ljava/io/BufferedReader;
    invoke-direct {v3, v2}, Ljava/io/BufferedReader;-><init>(Ljava/io/Reader;)V
    new-instance v4, Ljava/lang/StringBuilder;
    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    :loop_read
    invoke-virtual {v3}, Ljava/io/BufferedReader;->readLine()Ljava/lang/String;
    move-result-object v5
    if-eqz v5, :cond_read_done
    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v6, "\n"
    invoke-virtual {v4, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    goto :loop_read

    :cond_read_done
    invoke-virtual {v3}, Ljava/io/BufferedReader;->close()V
    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0

    :cond_empty
    const-string v0, ""
    return-object v0
    :try_end_http
    .catch Ljava/lang/Exception; {:try_start_http .. :try_end_http} :catch_http

    :catch_http
    const-string v0, ""
    return-object v0
.end method

.method public consumeNativeActions()Ljava/lang/String;
    .registers 5
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/AndroidBridge;->context:Landroid/content/Context;
    const-string v1, "nc_rpg_prefs"
    const/4 v2, 0x0
    invoke-virtual {v0, v1, v2}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
    move-result-object v1

    const-string v2, "native_action_queue"
    const-string v3, ""
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0

    invoke-interface {v1}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v1
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    invoke-interface {v1}, Landroid/content/SharedPreferences$Editor;->commit()Z

    return-object v0
.end method

.method public syncWidgetData(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V
    .registers 7
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/AndroidBridge;->context:Landroid/content/Context;
    const-string v1, "nc_rpg_prefs"
    const/4 v2, 0x0
    invoke-virtual {v0, v1, v2}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
    move-result-object v1

    invoke-interface {v1}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v1

    const-string v2, "widget_header_title"
    invoke-interface {v1, v2, p1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    const-string v2, "widget_header_sub"
    invoke-interface {v1, v2, p2}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    const-string v2, "widget_quests_lines"
    invoke-interface {v1, v2, p3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    invoke-interface {v1}, Landroid/content/SharedPreferences$Editor;->commit()Z

    invoke-static {v0}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->updateAllWidgets(Landroid/content/Context;)V
    return-void
.end method

.method public requestPinWidget()V
    .registers 6
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/AndroidBridge;->context:Landroid/content/Context;
    invoke-static {v0}, Landroid/appwidget/AppWidgetManager;->getInstance(Landroid/content/Context;)Landroid/appwidget/AppWidgetManager;
    move-result-object v1

    new-instance v2, Landroid/content/ComponentName;
    const-class v3, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;
    invoke-direct {v2, v0, v3}, Landroid/content/ComponentName;-><init>(Landroid/content/Context;Ljava/lang/Class;)V

    sget v3, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v4, 0x1a
    if-lt v3, v4, :cond_manual_toast

    invoke-virtual {v1}, Landroid/appwidget/AppWidgetManager;->isRequestPinAppWidgetSupported()Z
    move-result v3
    if-eqz v3, :cond_manual_toast

    const/4 v3, 0x0
    invoke-virtual {v1, v2, v3, v3}, Landroid/appwidget/AppWidgetManager;->requestPinAppWidget(Landroid/content/ComponentName;Landroid/os/Bundle;Landroid/app/PendingIntent;)Z
    move-result v3
    if-eqz v3, :cond_manual_toast

    invoke-static {v0}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->updateAllWidgets(Landroid/content/Context;)V
    return-void

    :cond_manual_toast
    const-string v1, "\ud83d\udcf1 Segure o dedo na Tela Inicial -> Widgets -> Night City RPG!"
    const/4 v2, 0x1
    invoke-static {v0, v1, v2}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v1
    invoke-virtual {v1}, Landroid/widget/Toast;->show()V
    return-void
.end method
