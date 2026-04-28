# Product Database & Ingredient Knowledge Module - Implementation Plan

## 1. Overview
This module upgrades the system from simple keyword matching to a **Knowledge Graph-based approach**. It connects **Skin Concerns** (Problems) to **Ingredients** (Solutions/Risks) to **Products** (Implementations).

## 2. Data Storage (Enhanced Models)

### A. Active Ingredient Model (`Ingredient`)
We will expand the existing `Ingredient` model to be the central knowledge node.
*   **Fields:**
    *   `name`: (e.g., "Retinol")
    *   `function`: (e.g., "Exfoliant", "Antioxidant")
    *   `benefits`: (e.g., "Increases cell turnover, reduces wrinkles") - Text or List.
    *   `side_effects`: (e.g., "Dryness, Sun sensitivity")
    *   `suitable_for`: (e.g., ["Oily", "Mature"]) - JSON or ManyToMany `SkinType`.
    *   `unsuitable_for`: (e.g., ["Sensitive", "Pregnant"]) - Critical for safety.

### B. Skin Concern Model (`SkinProblem`)
To allow dynamic management of problems.
*   **Fields:**
    *   `name`: (e.g., "Acne", "Hyper-pigmentation")
    *   `description`: Explanation of the condition.
    *   `recommended_ingredients`: ManyToMany to `Ingredient`.
    *   `avoid_ingredients`: ManyToMany to `Ingredient`.

### C. Product Enrichment
Existing `Product` model relationships will be strengthened.
*   `ingredients`: ManyToMany to `Ingredient` (Already exists, but needs full population).
*   `category`: Standardized choices (Cleanser, Toner, Serum, etc.).

## 3. Core Logic Logic

### A. The Matching Engine
Instead of checking `if 'Oily' in skin_type`, the engine will:
1.  Identify User Concerns (e.g., "Acne" from Computer Vision Score).
2.  Query `SkinProblem(name="Acne").recommended_ingredients`.
3.  Query `Product`s that contain these ingredients.

### B. The Safety Filter (Exclusion Logic)
1.  Identify User Constraints (e.g., "Sensitive Skin").
2.  Query `Ingredient.objects.filter(unsuitable_for__contains="Sensitive")`.
3.  **Exclude** any `Product` containing these ingredients.

## 4. Implementation Steps

1.  **Update `models.py`**: Add fields to `Ingredient` and create `SkinProblem`.
2.  **Seed Knowledge Base**: Create an admin script to populate common items:
    *   *Retinol*: Good for Aging, Bad for Sensitive.
    *   *Salicylic Acid*: Good for Acne, Bad for Dry.
3.  **Refactor `RecommendationEngine`**:
    *   Replace hardcoded `get_product("Salicylic")` with dynamic queries.
    *   `engine.get_safe_routine(user_profile)`
4.  **UI Update**:
    *   Show "Why this product?" badges (e.g., "Contains Niacinamide matching your Acne concern").
    *   Show "Ingredient Warnings" on Product Details page.

## 5. Benefits
*   **Personalization Depth**: Routines are built on chemical compatibility, not just marketing tags.
*   **Safety**: Automatically filters out allergens or irritants for sensitive users.
*   **Scalability**: Adding a new ingredient (e.g., "Snail Mucin") immediately updates recommendations without code changes.
