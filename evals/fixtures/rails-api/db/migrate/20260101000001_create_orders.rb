class CreateOrders < ActiveRecord::Migration[7.1]
  def change
    create_table :orders do |t|
      t.references :user, null: false, foreign_key: true
      t.integer :total_cents, null: false
      t.string :status, null: false, default: "pending"
      t.timestamps
    end

    add_index :orders, :user_id
    add_index :orders, :status
  end
end
