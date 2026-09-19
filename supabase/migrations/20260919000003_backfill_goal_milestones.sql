-- Add default milestones to goals that existed before the multi-goal feature.

insert into public.goal_milestones (goal_id, amount, title)
select g.id, round(g.target_amount * milestone.ratio, 2), milestone.title
from public.goals g
cross join (values
  (0.25::numeric, '25% milestone'),
  (0.50::numeric, '50% milestone'),
  (0.75::numeric, '75% milestone'),
  (1.00::numeric, 'Goal completed')
) as milestone(ratio, title)
where not exists (
  select 1 from public.goal_milestones existing where existing.goal_id = g.id
);
