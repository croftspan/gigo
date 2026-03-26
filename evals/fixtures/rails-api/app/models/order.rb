class Order < ApplicationRecord
  belongs_to :user

  validates :total_cents, presence: true, numericality: { greater_than: 0 }
  validates :status, presence: true, inclusion: { in: %w[pending confirmed shipped delivered cancelled] }

  scope :recent, -> { order(created_at: :desc).limit(10) }
end
