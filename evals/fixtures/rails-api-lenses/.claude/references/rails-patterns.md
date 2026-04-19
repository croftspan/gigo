# Rails Patterns — Deep Reference

Read this when working on migrations, endpoint design, or test architecture.

## Safe Migration Patterns

**Adding a column to a large table:**
1. `add_column :table, :column, :type` — no default, no null constraint
2. Backfill in a data migration or rake task
3. `change_column_default :table, :column, default_value`
4. `change_column_null :table, :column, false` (only after backfill)

**Adding an index on a large table:**
- Use `algorithm: :concurrently` inside `disable_ddl_transaction!`
- Never add a non-concurrent index on a table with >100k rows

**Renaming a column:**
- Don't. Add new column, migrate data, update code, drop old column across multiple PRs.

## N+1 Prevention

**In controllers:**
```ruby
# Bad — triggers N+1
@orders = user.orders
render json: @orders, include: :items

# Good — eager loads
@orders = user.orders.includes(:items)
render json: @orders, include: :items
```

**Detection:** Use Bullet gem in development/test. It raises on N+1 queries.

## Request Spec Patterns

```ruby
RSpec.describe "Orders API", type: :request do
  describe "GET /users/:user_id/orders" do
    it "returns paginated orders" do
      user = create(:user)
      create_list(:order, 30, user: user)

      get "/users/#{user.id}/orders", params: { page: 1, per_page: 10 }

      expect(response).to have_http_status(:ok)
      expect(json_response.length).to eq(10)
    end
  end
end
```

## Pagination

Use Pagy or Kaminari. Default 25 per page, max 100. Include `Link` headers for next/prev or a `meta.pagination` object in the response body.
