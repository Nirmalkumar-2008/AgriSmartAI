import os
import nbformat

roots = [
    r'C:\Users\Chanduru Kumar\.gemini\antigravity\scratch\AgriSmartAI',
    r'C:\Users\Chanduru Kumar\AgriSmartAI'
]

code1 = """models = {
    'Random Forest': RandomForestClassifier(n_estimators=40, max_depth=4, min_samples_leaf=3, max_features=0.55, class_weight='balanced', random_state=RANDOM_STATE),
    'CatBoost': CatBoostClassifier(iterations=28, depth=3, learning_rate=0.035, l2_leaf_reg=12, auto_class_weights='Balanced', random_seed=RANDOM_STATE, verbose=0),
    'Logistic Regression': LogisticRegression(C=0.5, max_iter=1000, random_state=RANDOM_STATE),
    'Support Vector Machine': SVC(C=1.0, kernel='rbf', gamma='scale', random_state=RANDOM_STATE),
    'Decision Tree': DecisionTreeClassifier(max_depth=4, min_samples_leaf=8, random_state=RANDOM_STATE),
    'XGBoost': XGBClassifier(n_estimators=25, max_depth=3, learning_rate=0.04, subsample=0.6, colsample_bytree=0.6, random_state=RANDOM_STATE, eval_metric='mlogloss')
}

results = []
fitted_models = {}
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

for name, model in models.items():
    use_scale = name in ['Support Vector Machine', 'Logistic Regression']
    X_tr_in = X_train_sc if use_scale else X_train.values
    X_te_in = X_test_sc if use_scale else X_test.values
    X_all_in = scaler.fit_transform(X) if use_scale else X.values
    
    model.fit(X_tr_in, y_train)
    y_pred = model.predict(X_te_in)
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1_w = f1_score(y_test, y_pred, average='weighted', zero_division=0)
    f1_m = f1_score(y_test, y_pred, average='macro', zero_division=0)
    
    cv_scores = cross_val_score(model, X_all_in, y, cv=skf, scoring='f1_macro')
    cv_str = f'{cv_scores.mean()*100:.2f}% ± {cv_scores.std()*100:.2f}%'
    
    results.append({
        'Model': name,
        'Accuracy': acc,
        'Precision': prec,
        'Recall': rec,
        'Weighted_F1': f1_w,
        'Macro_F1': f1_m,
        'CV_F1': cv_str
    })
    fitted_models[name] = model

df_res = pd.DataFrame(results).sort_values(by='Macro_F1', ascending=False).reset_index(drop=True)
display(df_res)"""

code2 = """best_row = df_res.iloc[0]
best_name = best_row['Model']
best_model = fitted_models[best_name]
use_scale = best_name in ['Support Vector Machine', 'Logistic Regression']
X_te_in = X_test_sc if use_scale else X_test.values
y_best_pred = best_model.predict(X_te_in)

print('='*50)
print('BEST FERTILIZER RECOMMENDATION MODEL')
print(f'Model: {best_name}')
print(f"Accuracy: {best_row['Accuracy']*100:.2f}%")
print(f"Weighted F1: {best_row['Weighted_F1']:.4f}")
print(f"Macro F1: {best_row['Macro_F1']:.4f}")
print('='*50)

cm = confusion_matrix(y_test, y_best_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Purples', xticklabels=fert_classes, yticklabels=fert_classes)
plt.title(f'Fertilizer Confusion Matrix ({best_name})')
plt.xlabel('Predicted')
plt.ylabel('True')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()"""

for root in roots:
    nb_path_04 = os.path.join(root, 'notebooks', '04_Fertilizer_Recommendation.ipynb')
    if os.path.exists(nb_path_04):
        with open(nb_path_04, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
        for cell in nb.cells:
            if cell.cell_type == 'code' and 'models = {' in cell.source:
                cell.source = code1
            elif cell.cell_type == 'code' and 'BEST FERTILIZER' in cell.source:
                cell.source = code2
        with open(nb_path_04, 'w', encoding='utf-8') as f:
            nbformat.write(nb, f)
        print('Successfully updated 04 notebook in', root)
