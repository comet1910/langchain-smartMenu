-- PostgreSQL 版本菜单数据库脚本
-- 使用前请先创建数据库: CREATE DATABASE menu;
-- 连接到数据库: \c menu;

-- 创建触发器函数（全局复用），自动更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- Table: menu_items
-- ============================================================
BEGIN;

DROP TABLE IF EXISTS menu_items;
CREATE TABLE menu_items (
  id SERIAL PRIMARY KEY,
  dish_name VARCHAR(100) NOT NULL,
  price DECIMAL(8, 2) NOT NULL,
  description TEXT,
  category VARCHAR(50) NOT NULL,
  spice_level SMALLINT DEFAULT 0,
  flavor VARCHAR(100) DEFAULT NULL,
  main_ingredients TEXT,
  cooking_method VARCHAR(50) DEFAULT NULL,
  is_vegetarian BOOLEAN DEFAULT FALSE,
  allergens VARCHAR(200) DEFAULT NULL,
  is_available BOOLEAN DEFAULT TRUE,
  is_featured BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE menu_items IS '菜单表';
COMMENT ON COLUMN menu_items.id IS '菜品ID，主键自增';
COMMENT ON COLUMN menu_items.dish_name IS '菜品名称';
COMMENT ON COLUMN menu_items.price IS '价格（元）';
COMMENT ON COLUMN menu_items.description IS '菜品描述';
COMMENT ON COLUMN menu_items.category IS '菜品分类';
COMMENT ON COLUMN menu_items.spice_level IS '辣度等级：0-不辣，1-微辣，2-中辣，3-重辣';
COMMENT ON COLUMN menu_items.flavor IS '口味特点';
COMMENT ON COLUMN menu_items.main_ingredients IS '主要食材，多个食材用逗号分隔';
COMMENT ON COLUMN menu_items.cooking_method IS '烹饪方法';
COMMENT ON COLUMN menu_items.is_vegetarian IS '是否素食：false-否，true-是';
COMMENT ON COLUMN menu_items.allergens IS '过敏原信息，多个过敏原用逗号分隔';
COMMENT ON COLUMN menu_items.is_available IS '是否可供应：false-不可用，true-可用';
COMMENT ON COLUMN menu_items.is_featured IS '是否特色主菜：false-否，true-是';
COMMENT ON COLUMN menu_items.created_at IS '创建时间';
COMMENT ON COLUMN menu_items.updated_at IS '更新时间';

CREATE INDEX IF NOT EXISTS idx_category ON menu_items(category);
CREATE INDEX IF NOT EXISTS idx_is_available ON menu_items(is_available);
CREATE INDEX IF NOT EXISTS idx_is_vegetarian ON menu_items(is_vegetarian);
CREATE INDEX IF NOT EXISTS idx_price ON menu_items(price);
CREATE INDEX IF NOT EXISTS idx_spice_level ON menu_items(spice_level);

DROP TRIGGER IF EXISTS trg_menu_items_updated_at ON menu_items;
CREATE TRIGGER trg_menu_items_updated_at
BEFORE UPDATE ON menu_items
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Records of menu_items
INSERT INTO menu_items (dish_name, price, description, category, spice_level, flavor, main_ingredients, cooking_method, is_vegetarian, allergens, is_available, is_featured)
VALUES
  ('宫保鸡丁', 28.00, '经典川菜，鸡肉丁配花生米，酸甜微辣，口感丰富', '川菜', 2, '酸甜微辣', '鸡胸肉,花生米,青椒,红椒,葱段', '爆炒', FALSE, '花生,可能含有麸质', TRUE, TRUE),
  ('麻婆豆腐', 18.00, '四川传统名菜，嫩滑豆腐配麻辣汤汁，下饭神器', '川菜', 3, '麻辣鲜香', '嫩豆腐,牛肉末,豆瓣酱,花椒', '烧炒', FALSE, '大豆,可能含有麸质', TRUE, FALSE),
  ('清炒时蔬', 15.00, '新鲜时令蔬菜清炒，营养健康，口感清爽', '素食', 0, '清淡爽口', '时令蔬菜,蒜蓉', '清炒', TRUE, NULL, TRUE, TRUE),
  ('红烧鲈鱼', 45.00, '新鲜鲈鱼红烧制作，肉质鲜美，营养丰富', '鲁菜', 1, '咸鲜微甜', '鲈鱼,生抽,老抽,冰糖,葱姜', '红烧', FALSE, '鱼类', TRUE, TRUE),
  ('蒜蓉西兰花', 12.00, '新鲜西兰花配蒜蓉，营养丰富，适合减肥人群', '素食', 0, '蒜香清淡', '西兰花,大蒜,橄榄油', '蒸炒', TRUE, '无过敏源', TRUE, FALSE);

-- 重置序列
SELECT setval('menu_items_id_seq', (SELECT MAX(id) FROM menu_items));

COMMIT;

-- ============================================================
-- Table: reservation_order
-- ============================================================
BEGIN;

DROP TABLE IF EXISTS reservation_order;
CREATE TABLE reservation_order (
  id SERIAL PRIMARY KEY,
  num_people INT NOT NULL,
  num_children INT NOT NULL,
  arrival_time TIMESTAMP NOT NULL,
  seat_preference VARCHAR(100) DEFAULT NULL,
  main_dish_preference VARCHAR(100) DEFAULT NULL,
  other_comments TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE reservation_order IS '预订单表';
COMMENT ON COLUMN reservation_order.id IS '预订单ID，主键自增';
COMMENT ON COLUMN reservation_order.num_people IS '客人人数';
COMMENT ON COLUMN reservation_order.num_children IS '儿童人数';
COMMENT ON COLUMN reservation_order.arrival_time IS '到达时间';
COMMENT ON COLUMN reservation_order.seat_preference IS '座位偏好';
COMMENT ON COLUMN reservation_order.main_dish_preference IS '主菜偏好';
COMMENT ON COLUMN reservation_order.other_comments IS '其他备注需求';
COMMENT ON COLUMN reservation_order.created_at IS '创建时间';
COMMENT ON COLUMN reservation_order.updated_at IS '更新时间';

DROP TRIGGER IF EXISTS trg_reservation_order_updated_at ON reservation_order;
CREATE TRIGGER trg_reservation_order_updated_at
BEFORE UPDATE ON reservation_order
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;
