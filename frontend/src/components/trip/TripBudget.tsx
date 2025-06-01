import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardHeader, Title2, Title3, Body1, Body2, Badge, Button, Input, Field } from '@fluentui/react-components';
import {
  CurrencyDollarIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  ArrowTrendingUpIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';

interface BudgetCategory {
  id: string;
  name: string;
  allocated: number;
  spent: number;
  color: string;
}

interface BudgetExpense {
  id: string;
  category_id: string;
  amount: number;
  description: string;
  date: string;
  paid_by: string;
  split_method: 'equal' | 'family_count' | 'custom';
}

interface TripBudgetProps {
  tripId: string;
  totalBudget: number;
  categories: BudgetCategory[];
  expenses: BudgetExpense[];
  families: Array<{ id: string; name: string }>;
  onUpdateBudget: (newBudget: number) => void;
  onAddCategory: (category: Omit<BudgetCategory, 'id'>) => void;
  onUpdateCategory: (categoryId: string, updates: Partial<BudgetCategory>) => void;
  onDeleteCategory: (categoryId: string) => void;
  onAddExpense: (expense: Omit<BudgetExpense, 'id'>) => void;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount);
};

const BudgetOverview: React.FC<{
  totalBudget: number;
  categories: BudgetCategory[];
  onUpdateBudget: (newBudget: number) => void;
}> = ({ totalBudget, categories, onUpdateBudget }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [newBudget, setNewBudget] = useState(totalBudget.toString());

  const totalAllocated = categories.reduce((sum, cat) => sum + cat.allocated, 0);
  const totalSpent = categories.reduce((sum, cat) => sum + cat.spent, 0);
  const remaining = totalBudget - totalSpent;
  const unallocated = totalBudget - totalAllocated;

  const handleSaveBudget = () => {
    const budget = parseFloat(newBudget);
    if (!isNaN(budget) && budget > 0) {
      onUpdateBudget(budget);
      setIsEditing(false);
    }
  };

  const pieData = categories.map((cat, index) => ({
    name: cat.name,
    value: cat.allocated,
    color: COLORS[index % COLORS.length],
  }));

  return (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <Title2>Budget Overview</Title2>
          <Button
            appearance="outline"
            icon={<PencilIcon className="w-4 h-4" />}
            onClick={() => setIsEditing(true)}
          >
            Edit Budget
          </Button>
        </div>
      </CardHeader>
      
      <div className="p-6">
        <div className="grid md:grid-cols-2 gap-6">
          {/* Budget Stats */}
          <div className="space-y-4">
            {/* Total Budget */}
            <div className="p-4 bg-primary-50 rounded-lg">
              {isEditing ? (
                <div className="space-y-2">
                  <Field label="Total Budget">
                    <Input
                      type="number"
                      value={newBudget}
                      onChange={(e) => setNewBudget(e.target.value)}
                      contentBefore={<CurrencyDollarIcon className="w-4 h-4" />}
                    />
                  </Field>
                  <div className="flex gap-2">
                    <Button size="small" onClick={handleSaveBudget}>Save</Button>
                    <Button 
                      size="small" 
                      appearance="outline" 
                      onClick={() => {
                        setIsEditing(false);
                        setNewBudget(totalBudget.toString());
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <>
                  <Title3 className="text-primary-600">{formatCurrency(totalBudget)}</Title3>
                  <Body2 className="text-primary-700">Total Budget</Body2>
                </>
              )}
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-green-50 rounded-lg text-center">
                <Title3 className="text-green-600">{formatCurrency(totalAllocated)}</Title3>
                <Body2 className="text-green-700">Allocated</Body2>
              </div>
              
              <div className="p-3 bg-amber-50 rounded-lg text-center">
                <Title3 className="text-amber-600">{formatCurrency(totalSpent)}</Title3>
                <Body2 className="text-amber-700">Spent</Body2>
              </div>
              
              <div className={`p-3 rounded-lg text-center ${remaining >= 0 ? 'bg-blue-50' : 'bg-red-50'}`}>
                <Title3 className={remaining >= 0 ? 'text-blue-600' : 'text-red-600'}>
                  {formatCurrency(Math.abs(remaining))}
                </Title3>
                <Body2 className={remaining >= 0 ? 'text-blue-700' : 'text-red-700'}>
                  {remaining >= 0 ? 'Remaining' : 'Over Budget'}
                </Body2>
              </div>
              
              <div className={`p-3 rounded-lg text-center ${unallocated >= 0 ? 'bg-neutral-50' : 'bg-red-50'}`}>
                <Title3 className={unallocated >= 0 ? 'text-neutral-600' : 'text-red-600'}>
                  {formatCurrency(Math.abs(unallocated))}
                </Title3>
                <Body2 className={unallocated >= 0 ? 'text-neutral-700' : 'text-red-700'}>
                  {unallocated >= 0 ? 'Unallocated' : 'Over Allocated'}
                </Body2>
              </div>
            </div>
          </div>

          {/* Budget Allocation Chart */}
          <div>
            <Title3 className="mb-4">Budget Allocation</Title3>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: any) => formatCurrency(value as number)} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-48 text-neutral-500">
                <Body1>No categories yet</Body1>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};

const BudgetCategories: React.FC<{
  categories: BudgetCategory[];
  onAddCategory: (category: Omit<BudgetCategory, 'id'>) => void;
  onUpdateCategory: (categoryId: string, updates: Partial<BudgetCategory>) => void;
  onDeleteCategory: (categoryId: string) => void;
}> = ({ categories, onAddCategory, onUpdateCategory: _onUpdateCategory, onDeleteCategory }) => {
  const [isAdding, setIsAdding] = useState(false);
  const [newCategory, setNewCategory] = useState({ name: '', allocated: 0 });

  const handleAddCategory = () => {
    if (newCategory.name.trim() && newCategory.allocated > 0) {
      onAddCategory({
        ...newCategory,
        spent: 0,
        color: COLORS[categories.length % COLORS.length],
      });
      setNewCategory({ name: '', allocated: 0 });
      setIsAdding(false);
    }
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <Title2>Budget Categories</Title2>
          <Button
            appearance="primary"
            icon={<PlusIcon className="w-4 h-4" />}
            onClick={() => setIsAdding(true)}
          >
            Add Category
          </Button>
        </div>
      </CardHeader>
      
      <div className="p-6">
        {/* Add Category Form */}
        {isAdding && (
          <Card className="mb-4 p-4 border-2 border-dashed border-primary-200">
            <div className="grid md:grid-cols-2 gap-4">
              <Field label="Category Name">
                <Input
                  value={newCategory.name}
                  onChange={(e) => setNewCategory({ ...newCategory, name: e.target.value })}
                  placeholder="e.g., Transportation, Food, Activities"
                />
              </Field>
              <Field label="Allocated Amount">
                <Input
                  type="number"
                  value={newCategory.allocated.toString()}
                  onChange={(e) => setNewCategory({ ...newCategory, allocated: parseFloat(e.target.value) || 0 })}
                  contentBefore={<CurrencyDollarIcon className="w-4 h-4" />}
                />
              </Field>
            </div>
            <div className="flex gap-2 mt-4">
              <Button onClick={handleAddCategory}>Add Category</Button>
              <Button appearance="outline" onClick={() => setIsAdding(false)}>Cancel</Button>
            </div>
          </Card>
        )}

        {/* Categories List */}
        <div className="space-y-4">
          {categories.map((category) => {
            const spentPercentage = category.allocated > 0 ? (category.spent / category.allocated) * 100 : 0;
            const isOverBudget = category.spent > category.allocated;

            return (
              <motion.div
                key={category.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Card className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div 
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: category.color }}
                      />
                      <Title3>{category.name}</Title3>
                      {isOverBudget && (
                        <Badge color="danger" icon={<ArrowTrendingUpIcon className="w-3 h-3" />}>
                          Over Budget
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Button 
                        appearance="outline" 
                        size="small"
                        icon={<PencilIcon className="w-3 h-3" />}
                      >
                        Edit
                      </Button>
                      <Button 
                        appearance="outline" 
                        size="small"
                        icon={<TrashIcon className="w-3 h-3" />}
                        onClick={() => onDeleteCategory(category.id)}
                      >
                        Delete
                      </Button>
                    </div>
                  </div>

                  <div className="grid md:grid-cols-3 gap-4 mb-3">
                    <div>
                      <Body2 className="text-neutral-600">Allocated</Body2>
                      <Body1 className="font-medium">{formatCurrency(category.allocated)}</Body1>
                    </div>
                    <div>
                      <Body2 className="text-neutral-600">Spent</Body2>
                      <Body1 className={`font-medium ${isOverBudget ? 'text-red-600' : ''}`}>
                        {formatCurrency(category.spent)}
                      </Body1>
                    </div>
                    <div>
                      <Body2 className="text-neutral-600">Remaining</Body2>
                      <Body1 className={`font-medium ${isOverBudget ? 'text-red-600' : 'text-green-600'}`}>
                        {formatCurrency(category.allocated - category.spent)}
                      </Body1>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full bg-neutral-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${
                        isOverBudget ? 'bg-red-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${Math.min(spentPercentage, 100)}%` }}
                    />
                  </div>
                  <Body2 className="text-neutral-500 text-xs mt-1">
                    {spentPercentage.toFixed(1)}% of budget used
                  </Body2>
                </Card>
              </motion.div>
            );
          })}
        </div>

        {/* Empty State */}
        {categories.length === 0 && !isAdding && (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-primary-50 rounded-full mx-auto mb-4 flex items-center justify-center">
              <ChartBarIcon className="w-8 h-8 text-primary-600" />
            </div>
            <Title3 className="text-neutral-900 mb-2">No budget categories</Title3>
            <Body1 className="text-neutral-600 mb-4">
              Start organizing your trip budget by creating categories
            </Body1>
            <Button
              appearance="primary"
              icon={<PlusIcon className="w-4 h-4" />}
              onClick={() => setIsAdding(true)}
            >
              Create First Category
            </Button>
          </div>
        )}
      </div>
    </Card>
  );
};

export const TripBudget: React.FC<TripBudgetProps> = ({
  tripId: _tripId,
  totalBudget,
  categories,
  expenses: _expenses,
  families: _families,
  onUpdateBudget,
  onAddCategory,
  onUpdateCategory: _onUpdateCategory,
  onDeleteCategory,
  onAddExpense: _onAddExpense,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="space-y-6"
    >
      <BudgetOverview
        totalBudget={totalBudget}
        categories={categories}
        onUpdateBudget={onUpdateBudget}
      />

      <BudgetCategories
        categories={categories}
        onAddCategory={onAddCategory}
        onUpdateCategory={_onUpdateCategory}
        onDeleteCategory={onDeleteCategory}
      />

      {/* Recent Expenses (placeholder) */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <Title2>Recent Expenses</Title2>
            <Button
              appearance="primary"
              icon={<PlusIcon className="w-4 h-4" />}
            >
              Add Expense
            </Button>
          </div>
        </CardHeader>
        
        <div className="p-6">
          <div className="text-center py-8">
            <Body1 className="text-neutral-600 mb-4">No expenses recorded yet</Body1>
            <Body2 className="text-neutral-500">
              Track your spending to stay within budget
            </Body2>
          </div>
        </div>
      </Card>
    </motion.div>
  );
};
