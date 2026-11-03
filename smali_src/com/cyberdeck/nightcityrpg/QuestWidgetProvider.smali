.class public Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;
.super Landroid/appwidget/AppWidgetProvider;

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Landroid/appwidget/AppWidgetProvider;-><init>()V
    return-void
.end method

.method public onUpdate(Landroid/content/Context;Landroid/appwidget/AppWidgetManager;[I)V
    .registers 4
    invoke-static {p1, p2, p3}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->updateWidgets(Landroid/content/Context;Landroid/appwidget/AppWidgetManager;[I)V
    return-void
.end method

.method public static updateAllWidgets(Landroid/content/Context;)V
    .registers 4
    invoke-static {p0}, Landroid/appwidget/AppWidgetManager;->getInstance(Landroid/content/Context;)Landroid/appwidget/AppWidgetManager;
    move-result-object v0
    new-instance v1, Landroid/content/ComponentName;
    const-class v2, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;
    invoke-direct {v1, p0, v2}, Landroid/content/ComponentName;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    invoke-virtual {v0, v1}, Landroid/appwidget/AppWidgetManager;->getAppWidgetIds(Landroid/content/ComponentName;)[I
    move-result-object v2
    invoke-static {p0, v0, v2}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->updateWidgets(Landroid/content/Context;Landroid/appwidget/AppWidgetManager;[I)V
    return-void
.end method

.method public onReceive(Landroid/content/Context;Landroid/content/Intent;)V
    .registers 12

    invoke-super {p0, p1, p2}, Landroid/appwidget/AppWidgetProvider;->onReceive(Landroid/content/Context;Landroid/content/Intent;)V
    if-eqz p2, :cond_done

    invoke-virtual {p2}, Landroid/content/Intent;->getAction()Ljava/lang/String;
    move-result-object v0
    if-eqz v0, :cond_done

    const-string v1, "nc_rpg_prefs"
    const/4 v2, 0x0
    invoke-virtual {p1, v1, v2}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
    move-result-object v1

    # Ação 1: [⏭ PRÓXIMA] -> Avança para a próxima Quest pendente no Widget
    const-string v3, "com.cyberdeck.nightcityrpg.WIDGET_NEXT"
    invoke-virtual {v3, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v3
    if-eqz v3, :cond_check_complete

    const-string v3, "widget_focus_idx"
    invoke-interface {v1, v3, v2}, Landroid/content/SharedPreferences;->getInt(Ljava/lang/String;I)I
    move-result v4
    add-int/lit8 v4, v4, 0x1
    invoke-interface {v1}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v5
    invoke-interface {v5, v3, v4}, Landroid/content/SharedPreferences$Editor;->putInt(Ljava/lang/String;I)Landroid/content/SharedPreferences$Editor;
    invoke-interface {v5}, Landroid/content/SharedPreferences$Editor;->commit()Z
    invoke-static {p1}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->updateAllWidgets(Landroid/content/Context;)V
    return-void

    :cond_check_complete
    # Ação 2: [✔ CONCLUIR] -> Conclui a Quest em destaque direto pela Tela Inicial e soma XP
    const-string v3, "com.cyberdeck.nightcityrpg.WIDGET_COMPLETE"
    invoke-virtual {v3, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v3
    if-eqz v3, :cond_check_refresh

    const-string v3, "widget_current_quest_id"
    const-string v4, ""
    invoke-interface {v1, v3, v4}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v3

    invoke-virtual {v3}, Ljava/lang/String;->length()I
    move-result v5
    if-lez v5, :cond_refresh_only

    # Enfileira complete:<questId> para o app sincronizar XP, atributos e log
    const-string v5, "native_action_queue"
    invoke-interface {v1, v5, v4}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v6

    new-instance v7, Ljava/lang/StringBuilder;
    invoke-direct {v7}, Ljava/lang/StringBuilder;-><init>()V
    invoke-virtual {v7, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v6, "complete:"
    invoke-virtual {v7, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v7, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v6, "\n"
    invoke-virtual {v7, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v7}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v6

    # Remove a linha concluída da lista imediata do Widget
    const-string v7, "widget_current_quest_line"
    invoke-interface {v1, v7, v4}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v7

    const-string v8, "widget_quests_lines"
    invoke-interface {v1, v8, v4}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v9

    invoke-virtual {v7}, Ljava/lang/String;->length()I
    move-result v3
    if-lez v3, :cond_save_queue

    new-instance v3, Ljava/lang/StringBuilder;
    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V
    invoke-virtual {v3, v7}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v10, "\n"
    invoke-virtual {v3, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v3

    invoke-virtual {v9, v3, v4}, Ljava/lang/String;->replace(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Ljava/lang/String;
    move-result-object v9
    invoke-virtual {v9, v7, v4}, Ljava/lang/String;->replace(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Ljava/lang/String;
    move-result-object v9
    invoke-virtual {v9}, Ljava/lang/String;->trim()Ljava/lang/String;
    move-result-object v9

    :cond_save_queue
    invoke-interface {v1}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v3
    invoke-interface {v3, v5, v6}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    invoke-interface {v3, v8, v9}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    invoke-interface {v3}, Landroid/content/SharedPreferences$Editor;->commit()Z

    const-string v3, "\u26a1 Miss\u00e3o conclu\u00edda pelo Widget! (+XP)"
    invoke-static {p1, v3, v2}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v3
    invoke-virtual {v3}, Landroid/widget/Toast;->show()V

    :cond_refresh_only
    invoke-static {p1}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->updateAllWidgets(Landroid/content/Context;)V
    return-void

    :cond_check_refresh
    const-string v3, "com.cyberdeck.nightcityrpg.WIDGET_REFRESH"
    invoke-virtual {v3, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v3
    if-eqz v3, :cond_done
    invoke-static {p1}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->updateAllWidgets(Landroid/content/Context;)V

    :cond_done
    return-void
.end method

.method public static updateWidgets(Landroid/content/Context;Landroid/appwidget/AppWidgetManager;[I)V
    .registers 16

    if-eqz p2, :cond_return
    array-length v0, p2
    if-lez v0, :cond_return

    const-string v0, "nc_rpg_prefs"
    const/4 v1, 0x0
    invoke-virtual {p0, v0, v1}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
    move-result-object v0

    const-string v2, "widget_header_title"
    const-string v3, "\u26a1 NIGHT CITY RPG \u00b7 LV 5 (520 XP)"
    invoke-interface {v0, v2, v3}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v2

    const-string v3, "widget_header_sub"
    const-string v4, "\ud83d\udef9 Street Kid \u00b7 \ud83d\udd25 Streak 1d \u00b7 Quests Ativas"
    invoke-interface {v0, v3, v4}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v3

    const-string v4, "widget_quests_lines"
    const-string v5, "rna_reator_pwr_avancar_30_min_no_modelo_mlp\t\ud83d\udd01 DAILY +10 XP \u00b7 \ud83e\udde0 INT\t\u2622\ufe0f RNA Reator PWR: Avan\u00e7ar 30 min no modelo MLP\nsoma_ler_1_artigo_ou_revisar_simulacao_de_cristais_piezoeletrico\t\ud83d\udd01 DAILY +10 XP \u00b7 \ud83e\udde0 INT\t\ud83d\udd0b SOMA: Ler 1 artigo ou revisar simula\u00e7\u00e3o de cristais piezoel\u00e9tricos\niff_revisar_materia_do_dia_checar_pendencias_do_suap\t\ud83d\udd01 DAILY +10 XP \u00b7 \ud83e\udde0 INT\t\ud83c\udf93 IFF: Revisar mat\u00e9ria do dia + checar pend\u00eancias do SUAP\norganizacao_atualizar_notas_do_obsidian_e_planejar_o_dia_seguint\t\ud83d\udd01 DAILY +10 XP \u00b7 \ud83d\ude0e COOL\t\ud83e\udde0 Organiza\u00e7\u00e3o: Atualizar notas e planejar o dia seguinte\nsaude_hidratacao_treino_ou_alongamento_diario\t\ud83d\udd01 DAILY +10 XP \u00b7 \ud83d\udcaa CORPO\t\ud83d\udcaa Sa\u00fade: Hidrata\u00e7\u00e3o + treino ou alongamento di\u00e1rio"
    invoke-interface {v0, v4, v5}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v4
    invoke-virtual {v4}, Ljava/lang/String;->trim()Ljava/lang/String;
    move-result-object v4

    const-string v5, "widget_focus_idx"
    invoke-interface {v0, v5, v1}, Landroid/content/SharedPreferences;->getInt(Ljava/lang/String;I)I
    move-result v5

    invoke-virtual {v4}, Ljava/lang/String;->length()I
    move-result v6
    if-lez v6, :cond_no_quests

    const-string v6, "\n"
    invoke-virtual {v4, v6}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;
    move-result-object v6
    array-length v7, v6
    if-lez v7, :cond_no_quests

    rem-int v5, v5, v7
    if-gez v5, :cond_idx_ok
    const/4 v5, 0x0
    :cond_idx_ok

    aget-object v8, v6, v5
    const-string v9, "\t"
    invoke-virtual {v8, v9}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;
    move-result-object v9
    array-length v10, v9
    const/4 v11, 0x3
    if-lt v10, v11, :cond_no_quests

    aget-object v10, v9, v1
    const/4 v11, 0x1
    aget-object v11, v9, v11
    const/4 v12, 0x2
    aget-object v12, v9, v12

    # Salva a quest atualmente focada no SharedPreferences para o botão [✔ CONCLUIR]
    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v9
    const-string v1, "widget_current_quest_id"
    invoke-interface {v9, v1, v10}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    const-string v1, "widget_current_quest_line"
    invoke-interface {v9, v1, v8}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    invoke-interface {v9}, Landroid/content/SharedPreferences$Editor;->commit()Z

    # Monta o texto da Quest em destaque (Spotlight)
    add-int/lit8 v8, v5, 0x1
    new-instance v9, Ljava/lang/StringBuilder;
    invoke-direct {v9}, Ljava/lang/StringBuilder;-><init>()V
    const-string v10, "\ud83c\udfaf ["
    invoke-virtual {v9, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v9, v8}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    const-string v8, "/"
    invoke-virtual {v9, v8}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v9, v7}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    const-string v8, "] "
    invoke-virtual {v9, v8}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v9, v11}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v8, "\n"
    invoke-virtual {v9, v8}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v9, v12}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v9}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v4

    # Monta a lista das próximas 2 missões pendentes abaixo do destaque
    const/4 v8, 0x1
    if-le v7, v8, :cond_single_quest

    add-int/lit8 v8, v5, 0x1
    rem-int/2addr v8, v7
    aget-object v8, v6, v8
    const-string v9, "\t"
    invoke-virtual {v8, v9}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;
    move-result-object v8
    const/4 v9, 0x2
    aget-object v8, v8, v9

    new-instance v9, Ljava/lang/StringBuilder;
    invoke-direct {v9}, Ljava/lang/StringBuilder;-><init>()V
    const-string v10, "\u2022 "
    invoke-virtual {v9, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v9, v8}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const/4 v8, 0x2
    if-le v7, v8, :cond_two_quests
    add-int/lit8 v8, v5, 0x2
    rem-int/2addr v8, v7
    aget-object v8, v6, v8
    const-string v10, "\t"
    invoke-virtual {v8, v10}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;
    move-result-object v8
    const/4 v10, 0x2
    aget-object v8, v8, v10
    const-string v10, "\n\u2022 "
    invoke-virtual {v9, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v9, v8}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    :cond_two_quests
    invoke-virtual {v9}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v5
    goto :cond_render_views

    :cond_single_quest
    const-string v5, "\u2728 \u00daltima miss\u00e3o pendente da fila!"
    goto :cond_render_views

    :cond_no_quests
    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v4
    const-string v5, "widget_current_quest_id"
    const-string v6, ""
    invoke-interface {v4, v5, v6}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    invoke-interface {v4}, Landroid/content/SharedPreferences$Editor;->commit()Z

    const-string v4, "\u2705 Todas as miss\u00f5es ativas foram conclu\u00eddas!"
    const-string v5, "Toque em [\u26a1 ABRIR APP] para adicionar novas Quests ou resetar o dia."

    :cond_render_views
    invoke-virtual {p0}, Landroid/content/Context;->getPackageName()Ljava/lang/String;
    move-result-object v6
    const/high16 v7, 0x7f020000
    new-instance v8, Landroid/widget/RemoteViews;
    invoke-direct {v8, v6, v7}, Landroid/widget/RemoteViews;-><init>(Ljava/lang/String;I)V

    const v6, 0x01020016
    invoke-virtual {v8, v6, v2}, Landroid/widget/RemoteViews;->setTextViewText(ILjava/lang/CharSequence;)V

    const v6, 0x01020010
    invoke-virtual {v8, v6, v3}, Landroid/widget/RemoteViews;->setTextViewText(ILjava/lang/CharSequence;)V

    const v6, 0x01020014
    invoke-virtual {v8, v6, v4}, Landroid/widget/RemoteViews;->setTextViewText(ILjava/lang/CharSequence;)V

    const v6, 0x01020015
    invoke-virtual {v8, v6, v5}, Landroid/widget/RemoteViews;->setTextViewText(ILjava/lang/CharSequence;)V

    # Flags de PendingIntent (FLAG_UPDATE_CURRENT | FLAG_IMMUTABLE em SDK >= 23)
    const/high16 v6, 0x08000000
    sget v7, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v9, 0x17
    if-lt v7, v9, :cond_pi_flags_ok
    const/high16 v6, 0x0c000000
    :cond_pi_flags_ok

    # Botão 1 (0x01020019): [✔ CONCLUIR]
    new-instance v7, Landroid/content/Intent;
    const-class v9, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;
    invoke-direct {v7, p0, v9}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    const-string v10, "com.cyberdeck.nightcityrpg.WIDGET_COMPLETE"
    invoke-virtual {v7, v10}, Landroid/content/Intent;->setAction(Ljava/lang/String;)Landroid/content/Intent;
    const/16 v10, 0x1b59
    invoke-static {p0, v10, v7, v6}, Landroid/app/PendingIntent;->getBroadcast(Landroid/content/Context;ILandroid/content/Intent;I)Landroid/app/PendingIntent;
    move-result-object v7
    const v10, 0x01020019
    invoke-virtual {v8, v10, v7}, Landroid/widget/RemoteViews;->setOnClickPendingIntent(ILandroid/app/PendingIntent;)V

    # Botão 2 (0x0102001a): [⏭ PRÓXIMA]
    new-instance v7, Landroid/content/Intent;
    invoke-direct {v7, p0, v9}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    const-string v10, "com.cyberdeck.nightcityrpg.WIDGET_NEXT"
    invoke-virtual {v7, v10}, Landroid/content/Intent;->setAction(Ljava/lang/String;)Landroid/content/Intent;
    const/16 v10, 0x1b5a
    invoke-static {p0, v10, v7, v6}, Landroid/app/PendingIntent;->getBroadcast(Landroid/content/Context;ILandroid/content/Intent;I)Landroid/app/PendingIntent;
    move-result-object v7
    const v10, 0x0102001a
    invoke-virtual {v8, v10, v7}, Landroid/widget/RemoteViews;->setOnClickPendingIntent(ILandroid/app/PendingIntent;)V

    # Botão 3 (0x0102001b) e Fundo (0x01020000): [⚡ ABRIR APP]
    new-instance v7, Landroid/content/Intent;
    const-class v9, Lcom/cyberdeck/nightcityrpg/MainActivity;
    invoke-direct {v7, p0, v9}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    const/high16 v9, 0x24000000
    invoke-virtual {v7, v9}, Landroid/content/Intent;->setFlags(I)Landroid/content/Intent;
    const/16 v9, 0x1b5b
    invoke-static {p0, v9, v7, v6}, Landroid/app/PendingIntent;->getActivity(Landroid/content/Context;ILandroid/content/Intent;I)Landroid/app/PendingIntent;
    move-result-object v7
    const v9, 0x0102001b
    invoke-virtual {v8, v9, v7}, Landroid/widget/RemoteViews;->setOnClickPendingIntent(ILandroid/app/PendingIntent;)V
    const v9, 0x01020000
    invoke-virtual {v8, v9, v7}, Landroid/widget/RemoteViews;->setOnClickPendingIntent(ILandroid/app/PendingIntent;)V

    invoke-virtual {p1, p2, v8}, Landroid/appwidget/AppWidgetManager;->updateAppWidget([ILandroid/widget/RemoteViews;)V

    :cond_return
    return-void
.end method
