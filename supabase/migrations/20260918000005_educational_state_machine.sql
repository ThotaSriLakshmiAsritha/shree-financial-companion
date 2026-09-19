update public.educational_context
set
  knowledge_state = case lower(trim(knowledge_state))
    when 'not_introduced' then 'NOT_INTRODUCED'
    when 'not introduced' then 'NOT_INTRODUCED'
    when 'introduced' then 'INTRODUCED'
    when 'basic_understanding' then 'BASIC_UNDERSTANDING'
    when 'basic understanding' then 'BASIC_UNDERSTANDING'
    when 'strong_understanding' then 'STRONG_UNDERSTANDING'
    when 'strong understanding' then 'STRONG_UNDERSTANDING'
    when 'successfully_applied' then 'SUCCESSFULLY_APPLIED'
    when 'successfully applied' then 'SUCCESSFULLY_APPLIED'
    when 'needs_clarification' then 'NEEDS_CLARIFICATION'
    when 'needs clarification' then 'NEEDS_CLARIFICATION'
    when 'misunderstood' then 'MISUNDERSTOOD'
    else 'INTRODUCED'
  end,
  application_state = case lower(trim(coalesce(application_state, '')))
    when 'not_observed' then 'NOT_OBSERVED'
    when 'not observed' then 'NOT_OBSERVED'
    when 'attempted' then 'ATTEMPTED'
    when 'needs practice' then 'ATTEMPTED'
    when 'successfully_applied' then 'SUCCESSFULLY_APPLIED'
    when 'successfully applied' then 'SUCCESSFULLY_APPLIED'
    when 'consistent' then 'SUCCESSFULLY_APPLIED'
    else 'NOT_OBSERVED'
  end;

alter table public.educational_context
  add constraint educational_context_knowledge_state_check
  check (knowledge_state in (
    'NOT_INTRODUCED',
    'INTRODUCED',
    'BASIC_UNDERSTANDING',
    'STRONG_UNDERSTANDING',
    'SUCCESSFULLY_APPLIED',
    'NEEDS_CLARIFICATION',
    'MISUNDERSTOOD'
  ));

alter table public.educational_context
  add constraint educational_context_application_state_check
  check (application_state is null or application_state in (
    'NOT_OBSERVED',
    'ATTEMPTED',
    'SUCCESSFULLY_APPLIED'
  ));
