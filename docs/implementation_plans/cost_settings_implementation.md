# Cost Settings Implementation Plan

## Phase 1: Database and Entity Layer

### 1.1 Database Models
- [ ] Update CostItem model in database:
  ```python
  class CostItem(Base):
      __tablename__ = 'cost_settings'
      id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      name = Column(String(100), nullable=False)
      type = Column(String(50), nullable=False)  # fuel, maintenance, etc.
      category = Column(String(50), nullable=False)  # base, variable, cargo-specific
      base_value = Column(Float, nullable=False)
      multiplier = Column(Float, nullable=False, default=1.0)
      currency = Column(String(3), nullable=False, default="EUR")
      is_enabled = Column(Boolean, nullable=False, default=True)
      description = Column(String(500))
      last_updated = Column(DateTime, nullable=False, default=datetime.utcnow)
  ```

### 1.2 Domain Entities
- [ ] Create CostSetting entity:
  ```python
  @dataclass
  class CostSetting:
      id: UUID
      name: str
      type: str
      category: str
      base_value: float
      multiplier: float = 1.0
      currency: str = "EUR"
      is_enabled: bool = True
      description: str = None
      last_updated: datetime = None
  ```

### 1.3 Repository Layer
- [ ] Add repository methods:
  - get_all_cost_settings()
  - get_enabled_cost_settings()
  - update_cost_settings(settings: List[CostSetting])
  - get_cost_setting_by_type(type: str)

## Phase 2: Service Layer

### 2.1 Cost Calculation Service
- [ ] Update CostCalculationService:
  - Add cost settings loading mechanism
  - Modify calculation methods to use settings
  - Add validation for settings
  - Add caching for frequently used settings

### 2.2 Cost Settings Service
- [ ] Create new CostSettingsService:
  ```python
  class CostSettingsService:
      def get_all_settings(self) -> List[CostSetting]
      def update_settings(self, settings: List[CostSetting]) -> bool
      def validate_settings(self, settings: List[CostSetting]) -> List[str]
      def get_default_settings(self) -> List[CostSetting]
  ```

### 2.3 Integration
- [ ] Update OfferService to use new cost calculation
- [ ] Add cost settings validation in RouteService

## Phase 3: API Layer

### 3.1 New Endpoints
- [ ] Add cost settings endpoints:
  ```python
  @app.route('/costs/settings', methods=['GET'])
  def get_cost_settings():
      """Return all cost settings"""

  @app.route('/costs/settings', methods=['POST'])
  def update_cost_settings():
      """Update cost settings"""

  @app.route('/costs/settings/defaults', methods=['GET'])
  def get_default_settings():
      """Get default cost settings"""
  ```

### 3.2 Update Existing Endpoints
- [ ] Modify cost calculation endpoint:
  ```python
  @app.route('/costs/<route_id>', methods=['POST'])
  def calculate_costs(route_id):
      """Calculate costs with detailed breakdown"""
  ```

### 3.3 Response DTOs
- [ ] Create response models:
  ```python
  @dataclass
  class CostSettingResponse:
      id: str
      type: str
      category: str
      base_value: float
      multiplier: float
      is_enabled: bool
      description: str

  @dataclass
  class CostBreakdownResponse:
      total_cost: float
      currency: str
      breakdown: Dict[str, Dict[str, float]]
      applied_settings: List[CostSettingResponse]
  ```

## Phase 4: Frontend Implementation

### 4.1 State Management
- [ ] Create cost settings store:
  ```typescript
  interface CostSettingsStore {
      settings: CostSetting[];
      loading: boolean;
      error: string | null;
      fetchSettings(): Promise<void>;
      updateSettings(settings: CostSetting[]): Promise<void>;
  }
  ```

### 4.2 Components
- [ ] Enhance AdvancedCostSettings component:
  - Add category grouping
  - Add validation
  - Add preview functionality
  - Improve error handling

- [ ] Create CostBreakdown component:
  ```typescript
  interface CostBreakdownProps {
      costs: CostBreakdown;
      appliedSettings: CostSetting[];
      onSettingClick?: (setting: CostSetting) => void;
  }
  ```

### 4.3 API Integration
- [ ] Create API client for cost settings:
  ```typescript
  class CostSettingsAPI {
      async getSettings(): Promise<CostSetting[]>;
      async updateSettings(settings: CostSetting[]): Promise<void>;
      async getDefaults(): Promise<CostSetting[]>;
  }
  ```

## Phase 5: Testing and Documentation

### 5.1 Backend Tests
- [ ] Unit tests:
  - CostSettingsService tests
  - Updated CostCalculationService tests
  - Repository layer tests
  - API endpoint tests

- [ ] Integration tests:
  - End-to-end cost calculation flow
  - Settings update scenarios
  - Error handling cases

### 5.2 Frontend Tests
- [ ] Component tests:
  - AdvancedCostSettings tests
  - CostBreakdown tests
  - Store tests

- [ ] Integration tests:
  - API integration tests
  - UI flow tests

### 5.3 Documentation
- [ ] API documentation:
  - New endpoints
  - Request/response formats
  - Error codes

- [ ] Frontend documentation:
  - Component usage
  - State management
  - API integration

## Phase 6: Deployment and Monitoring

### 6.1 Database Migration
- [ ] Create migration scripts:
  - Cost settings table updates
  - Default data population
  - Rollback procedures

### 6.2 Monitoring
- [ ] Add metrics:
  - Cost calculation performance
  - Settings update frequency
  - Error rates

### 6.3 Logging
- [ ] Enhanced logging:
  - Cost calculation details
  - Settings changes
  - Validation failures

## Implementation Order and Dependencies

1. Start with Database and Entity Layer (Phase 1)
2. Implement Service Layer changes (Phase 2)
3. Add API endpoints (Phase 3)
4. Develop Frontend components (Phase 4)
5. Add tests throughout development (Phase 5)
6. Prepare deployment and monitoring (Phase 6)

## Estimated Timeline

- Phase 1: 2 days
- Phase 2: 3 days
- Phase 3: 2 days
- Phase 4: 3 days
- Phase 5: 2 days
- Phase 6: 1 day

Total: ~13 working days

## Risk Mitigation

1. **Data Migration**
   - Create backup before migration
   - Test migration on staging
   - Prepare rollback plan

2. **Performance**
   - Implement caching where appropriate
   - Monitor calculation times
   - Optimize database queries

3. **User Experience**
   - Add clear error messages
   - Implement gradual rollout
   - Gather user feedback

## Success Criteria

1. All tests passing
2. Performance within acceptable ranges:
   - Cost calculation < 500ms
   - Settings update < 200ms
3. No regression in existing functionality
4. Successful user acceptance testing
