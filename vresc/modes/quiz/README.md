# Quiz Mode - Adaptive Financial Knowledge Assessment

## Overview

The Quiz Mode is an intelligent, adaptive assessment system built using Google's Agent Development Kit (ADK). It provides dynamic difficulty adjustment based on user performance and comprehensive financial knowledge testing capabilities.

## Architecture

### Core Components

#### 1. Quiz Manager Agent (`agent.py`)
- **Role**: Primary orchestrator for the entire quiz workflow
- **Model**: `gemini-2.5-pro`
- **Responsibilities**:
  - State management and quiz flow control
  - Rule-based decision making
  - Integration with subagents and tools
  - Dynamic difficulty adjustment
  - User feedback and interaction

#### 2. Subagents

##### Generator Agent (`subagents/generator/`)
- **Purpose**: Generates contextually appropriate quiz questions
- **Features**:
  - Adaptive difficulty based on user performance
  - Multiple question types (multiple choice, true/false, yes/no)
  - Content sourced from financial artifacts
  - Real-time question crafting

##### Summariser Agent (`subagents/summariser/`)
- **Purpose**: Creates comprehensive quiz performance summaries
- **Features**:
  - Performance analytics
  - Learning insights
  - Email integration capabilities (future)
  - Detailed score reporting

## State Management

The quiz system maintains comprehensive state tracking:

```python
{
    "q_state": True,                    # Quiz active state
    "no_q_asked": 0,                   # Number of questions asked
    "no_q_answered": 0,                # Number of questions answered
    "current_question": None,          # Current question object
    "points_scored": 0,                # User's current score
    "answers": [],                     # History of correct/incorrect
    "questions_asked": [],             # Question history
    "difficulty": "medium",            # Current difficulty level
    "current_outcome": None            # Last answer outcome
}
```

## Quiz Flow Logic

The Quiz Manager operates on a strict rule-based system with priority ordering:

### Rule 1 (Highest Priority): State Check
```
IF quiz_state is False:
    Transfer control to RootAgent
```

### Rule 2: Quiz Completion
```
IF answered_questions == 9:
    Provide final feedback
    Call Summariser Agent
    End quiz
```

### Rule 3: Question Generation
```
IF quiz_starting OR just_provided_feedback:
    Call Generator Agent immediately
```

### Rule 4: Answer Processing
```
IF user_provided_answer:
    Call oracler_tool with:
        - user_answer (normalized)
        - correct_answer
    Process response
```

### Rule 5: Feedback Delivery
```
IF oracler_tool_returned:
    Extract outcome from state
    Provide appropriate feedback
    Check difficulty adjustment
    Proceed to next question
```

## Difficulty Adaptation

The system implements intelligent difficulty scaling:

### Difficulty Levels
- **Easy**: Basic financial concepts
- **Medium**: Intermediate topics (default)
- **Hard**: Advanced financial analysis

### Adjustment Logic
- **Two consecutive correct answers**: Increase difficulty
- **Two consecutive incorrect answers**: Decrease difficulty
- **Bounded**: Cannot exceed "easy" to "hard" range

## Question Types

### Multiple Choice
- Format: a), b), c), d) options
- Answer normalization: Letter only (a, b, c, d)

### True/False
- Format: Boolean statements
- Answer normalization: "true" or "false"

### Yes/No
- Format: Confirmation questions
- Answer normalization: "yes" or "no"

## Tools

### Oracler Tool
The core assessment tool that:
- Compares user answers to correct answers
- Updates scoring and statistics
- Manages difficulty progression
- Tracks performance patterns

## Integration Points

### Artifacts
- **Summary**: Text-based financial content summary
- **Finance**: PDF financial documents
- Both loaded during quiz initialization

### Session State
All quiz data persists in session state for:
- Cross-agent communication
- State recovery
- Performance tracking
- Difficulty management

## Error Handling

### Answer Normalization
- Flexible input processing
- Case-insensitive matching
- Format standardization

### State Validation
- Continuous state integrity checks
- Graceful error recovery
- Transfer to RootAgent on critical failures

## Future Enhancements

### Planned Features
1. **Email Integration**: Automated summary delivery
2. **Advanced Analytics**: Detailed performance metrics
3. **Content Expansion**: Additional financial domains
4. **Personalization**: User-specific difficulty curves
5. **Progress Tracking**: Historical performance data

### Technical Improvements
1. **Enhanced Error Handling**: More robust state management
2. **Performance Optimization**: Faster question generation
3. **Content Management**: Dynamic artifact loading
4. **Integration APIs**: External learning management systems

## Development Guidelines

### Adding New Question Types
1. Update Generator Agent logic
2. Modify answer normalization in Quiz Manager
3. Test with oracler_tool integration
4. Update documentation

### Modifying Difficulty Logic
1. Adjust thresholds in oracler_tool
2. Update state management
3. Test edge cases (min/max difficulty)
4. Validate user experience

### Extending Analytics
1. Enhance Summariser Agent
2. Add new state tracking fields
3. Implement visualization capabilities
4. Integrate with external reporting

## Configuration

### Model Settings
- Primary model: `gemini-2.5-pro` (Quiz Manager)
- Configurable temperature and parameters
- Tool integration enabled

### Performance Parameters
- Quiz length: 9 questions (configurable)
- Difficulty adjustment: 2-answer threshold
- Default difficulty: "medium"

## Usage Examples

### Basic Quiz Initialization
```python
# Triggered via RootAgent with state_change tool
user_intent = "start_quiz"
# Loads artifacts and initializes state
```

### Custom Difficulty Setting
```python
# Modify initial state
session_state["difficulty"] = "hard"  # or "easy"
```

### Performance Monitoring
```python
# Access during quiz
current_score = session_state["points_scored"]
progress = session_state["no_q_answered"] / 9
```

This documentation should be updated as the Quiz Mode evolves and new features are implemented.